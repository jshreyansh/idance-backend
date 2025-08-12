#!/usr/bin/env python3
"""
Rate Limiting Utilities
Helper functions for rate limiting monitoring and management
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from .middleware import rate_limit_middleware
from .config import MONITORING_CONFIG

logger = logging.getLogger(__name__)

class RateLimitMonitor:
    """Monitor and analyze rate limiting activity"""
    
    def __init__(self):
        self.middleware = rate_limit_middleware
    
    async def get_recent_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent rate limit violations"""
        try:
            if not self.middleware.redis_client:
                return []
            
            violations_raw = self.middleware.redis_client.lrange('rate_limit_violations', 0, limit - 1)
            violations = []
            
            for violation_str in violations_raw:
                try:
                    violation = json.loads(violation_str)
                    violations.append(violation)
                except json.JSONDecodeError:
                    continue
            
            return violations
            
        except Exception as e:
            logger.error(f"Error getting recent violations: {e}")
            return []
    
    async def get_violation_stats(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get violation statistics for the specified time window"""
        try:
            violations = await self.get_recent_violations(1000)
            current_time = time.time()
            
            # Filter violations within time window
            recent_violations = [
                v for v in violations 
                if current_time - v.get('timestamp', 0) <= time_window
            ]
            
            stats = {
                'total_violations': len(recent_violations),
                'time_window': time_window,
                'violations_by_type': {},
                'violations_by_ip': {},
                'violations_by_endpoint': {},
                'violations_by_user': {},
                'top_violating_ips': [],
                'top_violating_endpoints': [],
            }
            
            # Analyze violations
            for violation in recent_violations:
                # By type
                v_type = violation.get('violation_type', 'unknown')
                stats['violations_by_type'][v_type] = stats['violations_by_type'].get(v_type, 0) + 1
                
                # By IP
                ip = violation.get('ip', 'unknown')
                stats['violations_by_ip'][ip] = stats['violations_by_ip'].get(ip, 0) + 1
                
                # By endpoint
                endpoint = violation.get('endpoint', 'unknown')
                stats['violations_by_endpoint'][endpoint] = stats['violations_by_endpoint'].get(endpoint, 0) + 1
                
                # By user
                user_id = violation.get('user_id')
                if user_id:
                    stats['violations_by_user'][user_id] = stats['violations_by_user'].get(user_id, 0) + 1
            
            # Top violators
            stats['top_violating_ips'] = sorted(
                stats['violations_by_ip'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            stats['top_violating_endpoints'] = sorted(
                stats['violations_by_endpoint'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting violation stats: {e}")
            return {'error': str(e)}
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get currently blocked IPs"""
        try:
            if not self.middleware.redis_client:
                return []
            
            blocked_ips = []
            
            # Scan for blocked IP keys
            for key in self.middleware.redis_client.scan_iter(match="blocked_ip:*"):
                ip = key.replace("blocked_ip:", "")
                block_data_str = self.middleware.redis_client.get(key)
                
                if block_data_str:
                    try:
                        block_data = json.loads(block_data_str)
                        ttl = self.middleware.redis_client.ttl(key)
                        
                        blocked_ips.append({
                            'ip': ip,
                            'blocked_at': block_data.get('blocked_at'),
                            'violation_count': block_data.get('violation_count'),
                            'offense_count': block_data.get('offense_count'),
                            'duration': block_data.get('duration'),
                            'remaining_time': ttl if ttl > 0 else 0
                        })
                    except json.JSONDecodeError:
                        continue
            
            return blocked_ips
            
        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")
            return []
    
    async def unblock_ip(self, ip: str) -> bool:
        """Manually unblock an IP address"""
        try:
            if not self.middleware.redis_client:
                return False
            
            key = f"blocked_ip:{ip}"
            result = self.middleware.redis_client.delete(key)
            
            if result:
                logger.info(f"✅ Manually unblocked IP: {ip}")
                return True
            else:
                logger.warning(f"⚠️ IP {ip} was not blocked")
                return False
                
        except Exception as e:
            logger.error(f"Error unblocking IP {ip}: {e}")
            return False
    
    async def check_for_attacks(self) -> Dict[str, Any]:
        """Check for potential DDoS attacks or abuse patterns"""
        try:
            stats = await self.get_violation_stats(3600)  # Last hour
            alerts = []
            
            # Check for high violation rate
            total_violations = stats.get('total_violations', 0)
            if total_violations >= MONITORING_CONFIG['high_violation_rate']['threshold']:
                alerts.append({
                    'type': 'high_violation_rate',
                    'severity': 'warning',
                    'message': f"High violation rate detected: {total_violations} violations in the last hour",
                    'data': {'violations': total_violations}
                })
            
            # Check for potential DDoS
            recent_stats = await self.get_violation_stats(60)  # Last minute
            recent_violations = recent_stats.get('total_violations', 0)
            if recent_violations >= MONITORING_CONFIG['ddos_detection']['threshold']:
                alerts.append({
                    'type': 'ddos_detection',
                    'severity': 'critical',
                    'message': f"Potential DDoS attack detected: {recent_violations} violations in the last minute",
                    'data': {'violations': recent_violations}
                })
            
            # Check for suspicious IPs
            for ip, violation_count in stats.get('top_violating_ips', [])[:5]:
                if violation_count >= MONITORING_CONFIG['suspicious_ip']['threshold']:
                    alerts.append({
                        'type': 'suspicious_ip',
                        'severity': 'warning',
                        'message': f"Suspicious IP activity: {ip} with {violation_count} violations",
                        'data': {'ip': ip, 'violations': violation_count}
                    })
            
            return {
                'timestamp': time.time(),
                'alerts': alerts,
                'stats_summary': {
                    'total_violations_hour': total_violations,
                    'total_violations_minute': recent_violations,
                    'blocked_ips_count': len(await self.get_blocked_ips()),
                    'top_violating_ip': stats.get('top_violating_ips', [None])[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking for attacks: {e}")
            return {'error': str(e)}
    
    async def get_rate_limit_health(self) -> Dict[str, Any]:
        """Get rate limiting system health status"""
        try:
            health = {
                'redis_connected': False,
                'redis_info': None,
                'active_blocks': 0,
                'recent_violations': 0,
                'system_status': 'unknown'
            }
            
            if self.middleware.redis_client:
                try:
                    # Test Redis connection
                    self.middleware.redis_client.ping()
                    health['redis_connected'] = True
                    
                    # Get Redis info
                    redis_info = self.middleware.redis_client.info()
                    health['redis_info'] = {
                        'used_memory_human': redis_info.get('used_memory_human'),
                        'connected_clients': redis_info.get('connected_clients'),
                        'total_commands_processed': redis_info.get('total_commands_processed')
                    }
                    
                    # Get active blocks
                    blocked_ips = await self.get_blocked_ips()
                    health['active_blocks'] = len(blocked_ips)
                    
                    # Get recent violations
                    recent_stats = await self.get_violation_stats(300)  # Last 5 minutes
                    health['recent_violations'] = recent_stats.get('total_violations', 0)
                    
                    # Determine system status
                    if health['recent_violations'] > 100:
                        health['system_status'] = 'high_load'
                    elif health['active_blocks'] > 10:
                        health['system_status'] = 'active_blocking'
                    else:
                        health['system_status'] = 'healthy'
                        
                except Exception as e:
                    health['redis_connected'] = False
                    health['error'] = str(e)
                    health['system_status'] = 'redis_error'
            else:
                health['system_status'] = 'disabled'
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting rate limit health: {e}")
            return {'error': str(e), 'system_status': 'error'}

# Global monitor instance
rate_limit_monitor = RateLimitMonitor()

# Utility functions
async def get_current_rate_limits(ip: str, user_id: Optional[str] = None, endpoint: str = "general") -> Dict[str, Any]:
    """Get current rate limit status for debugging"""
    return await rate_limit_middleware.get_rate_limit_info(ip, user_id, endpoint)

async def clear_rate_limits(ip: Optional[str] = None, user_id: Optional[str] = None, endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Clear rate limits (for testing/admin purposes)"""
    try:
        if not rate_limit_middleware.redis_client:
            return {'error': 'Redis not available'}
        
        cleared = 0
        
        if ip and endpoint:
            key = f"rate_limit:ip:{ip}:{endpoint}"
            if rate_limit_middleware.redis_client.delete(key):
                cleared += 1
        
        if user_id and endpoint:
            key = f"rate_limit:user:{user_id}:{endpoint}"
            if rate_limit_middleware.redis_client.delete(key):
                cleared += 1
        
        if ip and not endpoint:
            # Clear all limits for IP
            for key in rate_limit_middleware.redis_client.scan_iter(match=f"rate_limit:ip:{ip}:*"):
                if rate_limit_middleware.redis_client.delete(key):
                    cleared += 1
        
        if user_id and not endpoint:
            # Clear all limits for user
            for key in rate_limit_middleware.redis_client.scan_iter(match=f"rate_limit:user:{user_id}:*"):
                if rate_limit_middleware.redis_client.delete(key):
                    cleared += 1
        
        return {'cleared': cleared, 'message': f'Cleared {cleared} rate limit entries'}
        
    except Exception as e:
        logger.error(f"Error clearing rate limits: {e}")
        return {'error': str(e)}