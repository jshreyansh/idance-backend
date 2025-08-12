#!/usr/bin/env python3
"""
Rate Limiting Middleware
Core rate limiting functionality using Redis for storage
"""

import redis
import time
import json
import os
import logging
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, HTTPException
from .config import RATE_LIMIT_CONFIG, DDOS_PROTECTION, REDIS_CONFIG, WHITELIST_IPS, ENVIRONMENT_MULTIPLIERS

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """Rate limiting middleware with Redis backend"""
    
    def __init__(self):
        """Initialize Redis connection and configuration"""
        try:
            # Get environment
            self.environment = os.getenv('ENVIRONMENT', 'development')
            self.multiplier = ENVIRONMENT_MULTIPLIERS.get(self.environment, 1.0)
            
            # Initialize Redis client
            redis_host = os.getenv('REDIS_HOST', REDIS_CONFIG['host'])
            redis_port = int(os.getenv('REDIS_PORT', REDIS_CONFIG['port']))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=REDIS_CONFIG['db'],
                decode_responses=REDIS_CONFIG['decode_responses'],
                socket_connect_timeout=REDIS_CONFIG['socket_connect_timeout'],
                socket_timeout=REDIS_CONFIG['socket_timeout'],
                retry_on_timeout=REDIS_CONFIG['retry_on_timeout'],
                health_check_interval=REDIS_CONFIG['health_check_interval']
            )
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected successfully for rate limiting (Environment: {self.environment})")
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Rate limiting will be disabled.")
            self.redis_client = None
        except Exception as e:
            logger.error(f"❌ Error initializing rate limiting: {e}")
            self.redis_client = None
    
    async def check_rate_limit(self, request: Request, endpoint: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check rate limits for IP and user
        Returns dict with 'allowed': bool and rate limit info
        """
        if not self.redis_client:
            # If Redis is not available, allow all requests but log warning
            logger.warning("Rate limiting disabled - Redis not available")
            return {'allowed': True, 'reason': 'redis_unavailable'}
        
        client_ip = self._get_client_ip(request)
        
        # Check if IP is whitelisted
        if client_ip in WHITELIST_IPS:
            return {'allowed': True, 'reason': 'whitelisted_ip'}
        
        # Check if IP is blocked
        if await self._is_ip_blocked(client_ip):
            return {
                'allowed': False, 
                'reason': 'ip_blocked',
                'retry_after': DDOS_PROTECTION['block_duration']
            }
        
        # Check burst protection first
        if not await self._check_burst_limit(client_ip):
            await self._track_violation(client_ip, user_id, endpoint, 'burst_limit')
            return {
                'allowed': False,
                'reason': 'burst_limit_exceeded',
                'retry_after': DDOS_PROTECTION['burst_limit']['window']
            }
        
        # Check IP rate limit
        ip_check = await self._check_ip_rate_limit(client_ip, endpoint)
        if not ip_check['allowed']:
            await self._track_violation(client_ip, user_id, endpoint, 'ip_rate_limit')
            return ip_check
        
        # Check user rate limit if user is authenticated
        if user_id:
            user_check = await self._check_user_rate_limit(user_id, endpoint)
            if not user_check['allowed']:
                await self._track_violation(client_ip, user_id, endpoint, 'user_rate_limit')
                return user_check
        
        return {'allowed': True, 'reason': 'within_limits'}
    
    async def _check_ip_rate_limit(self, ip: str, endpoint: str) -> Dict[str, Any]:
        """Check IP-based rate limit"""
        key = f"rate_limit:ip:{ip}:{endpoint}"
        limit = self._get_limit_for_endpoint(endpoint, 'ip')
        
        if not limit:
            return {'allowed': True, 'reason': 'no_ip_limit'}
        
        return await self._check_limit(key, limit, 'ip_rate_limit')
    
    async def _check_user_rate_limit(self, user_id: str, endpoint: str) -> Dict[str, Any]:
        """Check user-based rate limit"""
        key = f"rate_limit:user:{user_id}:{endpoint}"
        limit = self._get_limit_for_endpoint(endpoint, 'user')
        
        if not limit:
            return {'allowed': True, 'reason': 'no_user_limit'}
        
        return await self._check_limit(key, limit, 'user_rate_limit')
    
    async def _check_burst_limit(self, ip: str) -> bool:
        """Check burst rate limiting"""
        try:
            key = f"burst:{ip}"
            burst_config = DDOS_PROTECTION['burst_limit']
            current = self.redis_client.get(key)
            
            if current and int(current) >= burst_config['requests']:
                return False
            
            # Increment and set expiry
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, burst_config['window'])
            pipe.execute()
            
            return True
        except Exception as e:
            logger.error(f"Error checking burst limit: {e}")
            return True  # Allow on error
    
    async def _check_limit(self, key: str, limit: str, limit_type: str) -> Dict[str, Any]:
        """Check if request is within rate limit"""
        try:
            count, window = self._parse_limit(limit)
            
            # Apply environment multiplier
            count = int(count * self.multiplier)
            
            current = self.redis_client.get(key)
            current_count = int(current) if current else 0
            
            if current_count >= count:
                return {
                    'allowed': False,
                    'reason': limit_type,
                    'limit': count,
                    'current': current_count,
                    'retry_after': window
                }
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            result = pipe.execute()
            
            new_count = result[0]
            remaining = max(0, count - new_count)
            reset_time = int(time.time()) + window
            
            return {
                'allowed': True,
                'reason': 'within_limits',
                'limit': count,
                'current': new_count,
                'remaining': remaining,
                'reset_time': reset_time
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {'allowed': True, 'reason': 'error_checking_limit'}
    
    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        try:
            key = f"blocked_ip:{ip}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking IP block status: {e}")
            return False
    
    async def _track_violation(self, ip: str, user_id: Optional[str], endpoint: str, violation_type: str):
        """Track rate limit violations for monitoring and blocking"""
        try:
            violation = {
                'ip': ip,
                'user_id': user_id,
                'endpoint': endpoint,
                'violation_type': violation_type,
                'timestamp': time.time(),
                'environment': self.environment
            }
            
            # Store violation for monitoring
            self.redis_client.lpush('rate_limit_violations', json.dumps(violation))
            self.redis_client.ltrim('rate_limit_violations', 0, 9999)  # Keep last 10k
            
            # Track IP violations for potential blocking
            ip_violations_key = f"ip_violations:{ip}"
            violations_count = self.redis_client.incr(ip_violations_key)
            self.redis_client.expire(ip_violations_key, DDOS_PROTECTION['violation_window'])
            
            # Block IP if too many violations
            if violations_count >= DDOS_PROTECTION['ip_block_threshold']:
                await self._block_ip(ip, violations_count)
            
            logger.warning(f"Rate limit violation: {violation}")
            
        except Exception as e:
            logger.error(f"Error tracking violation: {e}")
    
    async def _block_ip(self, ip: str, violation_count: int):
        """Block IP address based on violation count"""
        try:
            # Determine block duration based on offense count
            offense_key = f"ip_offenses:{ip}"
            offense_count = self.redis_client.incr(offense_key)
            self.redis_client.expire(offense_key, 86400 * 7)  # Track offenses for 7 days
            
            if offense_count == 1:
                duration = DDOS_PROTECTION['progressive_blocks']['first_offense']
            elif offense_count == 2:
                duration = DDOS_PROTECTION['progressive_blocks']['second_offense']
            elif offense_count == 3:
                duration = DDOS_PROTECTION['progressive_blocks']['third_offense']
            else:
                duration = DDOS_PROTECTION['progressive_blocks']['repeat_offender']
            
            # Block the IP
            block_key = f"blocked_ip:{ip}"
            self.redis_client.setex(block_key, duration, json.dumps({
                'blocked_at': time.time(),
                'violation_count': violation_count,
                'offense_count': offense_count,
                'duration': duration
            }))
            
            logger.warning(f"🚫 IP {ip} blocked for {duration} seconds (offense #{offense_count}, {violation_count} violations)")
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _parse_limit(self, limit: str) -> Tuple[int, int]:
        """Parse limit string (e.g., '100/minute') into count and window seconds"""
        try:
            count_str, period = limit.split('/')
            count = int(count_str)
            
            period_mapping = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            
            window = period_mapping.get(period, 60)  # Default to minute
            return count, window
            
        except Exception as e:
            logger.error(f"Error parsing limit '{limit}': {e}")
            return 100, 60  # Default fallback
    
    def _get_limit_for_endpoint(self, endpoint: str, limit_type: str) -> Optional[str]:
        """Get rate limit for specific endpoint and type"""
        endpoint_config = RATE_LIMIT_CONFIG.get(endpoint)
        if endpoint_config:
            return endpoint_config.get(limit_type)
        return None
    
    async def get_rate_limit_info(self, ip: str, user_id: Optional[str], endpoint: str) -> Dict[str, Any]:
        """Get current rate limit status for debugging"""
        try:
            info = {
                'ip': ip,
                'user_id': user_id,
                'endpoint': endpoint,
                'environment': self.environment,
                'multiplier': self.multiplier,
                'is_blocked': await self._is_ip_blocked(ip),
                'limits': {}
            }
            
            # Get IP limit info
            ip_limit = self._get_limit_for_endpoint(endpoint, 'ip')
            if ip_limit:
                ip_key = f"rate_limit:ip:{ip}:{endpoint}"
                ip_current = self.redis_client.get(ip_key)
                count, window = self._parse_limit(ip_limit)
                adjusted_count = int(count * self.multiplier)
                
                info['limits']['ip'] = {
                    'limit': ip_limit,
                    'adjusted_limit': adjusted_count,
                    'current': int(ip_current) if ip_current else 0,
                    'remaining': max(0, adjusted_count - (int(ip_current) if ip_current else 0))
                }
            
            # Get user limit info
            if user_id:
                user_limit = self._get_limit_for_endpoint(endpoint, 'user')
                if user_limit:
                    user_key = f"rate_limit:user:{user_id}:{endpoint}"
                    user_current = self.redis_client.get(user_key)
                    count, window = self._parse_limit(user_limit)
                    adjusted_count = int(count * self.multiplier)
                    
                    info['limits']['user'] = {
                        'limit': user_limit,
                        'adjusted_limit': adjusted_count,
                        'current': int(user_current) if user_current else 0,
                        'remaining': max(0, adjusted_count - (int(user_current) if user_current else 0))
                    }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {'error': str(e)}

# Global instance
rate_limit_middleware = RateLimitMiddleware()