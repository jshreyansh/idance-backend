#!/usr/bin/env python3
"""
Rate Limiting Admin Endpoints
Administrative endpoints for monitoring and managing rate limits
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from services.user.service import get_current_user_id
from .utils import rate_limit_monitor, get_current_rate_limits, clear_rate_limits
from .middleware import rate_limit_middleware
from .decorators import public_rate_limit, protected_rate_limit

rate_limit_admin_router = APIRouter()

@rate_limit_admin_router.get('/api/rate-limits/health')
@public_rate_limit('health_check')
async def get_rate_limit_health(request: Request):
    """Get rate limiting system health status"""
    try:
        health = await rate_limit_monitor.get_rate_limit_health()
        return JSONResponse(
            content=health,
            status_code=200 if health.get('system_status') == 'healthy' else 503
        )
    except Exception as e:
        return JSONResponse(
            content={'error': str(e), 'system_status': 'error'},
            status_code=500
        )

@rate_limit_admin_router.get('/api/rate-limits/status')
@protected_rate_limit('user_stats')
async def get_rate_limit_status(
    request: Request,
    endpoint: Optional[str] = Query(None, description="Specific endpoint to check"),
    user_id: str = Depends(get_current_user_id)
):
    """Get current rate limit status for the authenticated user"""
    try:
        client_ip = rate_limit_middleware._get_client_ip(request)
        
        # If no endpoint specified, use a general one
        if not endpoint:
            endpoint = "general"
        
        info = await get_current_rate_limits(client_ip, user_id, endpoint)
        
        return JSONResponse(content=info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rate limit status: {str(e)}")

@rate_limit_admin_router.get('/api/rate-limits/violations')
@protected_rate_limit('user_stats')
async def get_recent_violations(
    request: Request,
    limit: int = Query(50, description="Number of recent violations to retrieve"),
    user_id: str = Depends(get_current_user_id)
):
    """Get recent rate limit violations (admin functionality)"""
    try:
        violations = await rate_limit_monitor.get_recent_violations(limit)
        return JSONResponse(content={'violations': violations, 'count': len(violations)})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting violations: {str(e)}")

@rate_limit_admin_router.get('/api/rate-limits/stats')
@protected_rate_limit('user_stats')
async def get_violation_stats(
    request: Request,
    window: int = Query(3600, description="Time window in seconds (default: 1 hour)"),
    user_id: str = Depends(get_current_user_id)
):
    """Get violation statistics for the specified time window"""
    try:
        stats = await rate_limit_monitor.get_violation_stats(window)
        return JSONResponse(content=stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting violation stats: {str(e)}")

@rate_limit_admin_router.get('/api/rate-limits/blocked-ips')
@protected_rate_limit('user_stats')
async def get_blocked_ips(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Get currently blocked IP addresses"""
    try:
        blocked_ips = await rate_limit_monitor.get_blocked_ips()
        return JSONResponse(content={'blocked_ips': blocked_ips, 'count': len(blocked_ips)})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting blocked IPs: {str(e)}")

@rate_limit_admin_router.post('/api/rate-limits/unblock-ip')
@protected_rate_limit('profile_update')
async def unblock_ip(
    request: Request,
    ip: str = Query(..., description="IP address to unblock"),
    user_id: str = Depends(get_current_user_id)
):
    """Manually unblock an IP address (admin functionality)"""
    try:
        # Note: In a real application, you'd want to check if the user has admin privileges
        success = await rate_limit_monitor.unblock_ip(ip)
        
        if success:
            return JSONResponse(content={'message': f'Successfully unblocked IP: {ip}'})
        else:
            return JSONResponse(content={'message': f'IP {ip} was not blocked'}, status_code=404)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unblocking IP: {str(e)}")

@rate_limit_admin_router.post('/api/rate-limits/clear')
@protected_rate_limit('profile_update')
async def clear_rate_limits_endpoint(
    request: Request,
    ip: Optional[str] = Query(None, description="IP address to clear limits for"),
    endpoint: Optional[str] = Query(None, description="Specific endpoint to clear limits for"),
    user_id: str = Depends(get_current_user_id)
):
    """Clear rate limits for testing/admin purposes"""
    try:
        # Note: In a real application, you'd want to check if the user has admin privileges
        result = await clear_rate_limits(ip, user_id, endpoint)
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing rate limits: {str(e)}")

@rate_limit_admin_router.get('/api/rate-limits/attack-detection')
@protected_rate_limit('user_stats')
async def check_attack_detection(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Check for potential attacks or suspicious activity"""
    try:
        attack_info = await rate_limit_monitor.check_for_attacks()
        return JSONResponse(content=attack_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking for attacks: {str(e)}")

@rate_limit_admin_router.get('/api/rate-limits/config')
@public_rate_limit('health_check')
async def get_rate_limit_config(request: Request):
    """Get current rate limiting configuration (public info only)"""
    try:
        from .config import RATE_LIMIT_CONFIG, ENVIRONMENT_MULTIPLIERS
        import os
        
        environment = os.getenv('ENVIRONMENT', 'development')
        multiplier = ENVIRONMENT_MULTIPLIERS.get(environment, 1.0)
        
        # Return sanitized config info
        config_info = {
            'environment': environment,
            'multiplier': multiplier,
            'endpoints': {}
        }
        
        # Add public endpoint info (without exact limits for security)
        for endpoint, limits in RATE_LIMIT_CONFIG.items():
            config_info['endpoints'][endpoint] = {
                'has_ip_limit': bool(limits.get('ip')),
                'has_user_limit': bool(limits.get('user')),
                'category': _get_endpoint_category(endpoint)
            }
        
        return JSONResponse(content=config_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")

def _get_endpoint_category(endpoint: str) -> str:
    """Get category for an endpoint"""
    if endpoint.startswith('auth_'):
        return 'authentication'
    elif endpoint.startswith('upload_'):
        return 'file_upload'
    elif endpoint.startswith('ai_'):
        return 'ai_processing'
    elif endpoint.startswith('challenge_'):
        return 'challenges'
    elif endpoint.startswith('session_'):
        return 'sessions'
    elif endpoint in ['health_check', 'public_data']:
        return 'public'
    else:
        return 'general'

# Health check endpoint specifically for rate limiting
@rate_limit_admin_router.get('/api/rate-limits/ping')
async def ping_rate_limits(request: Request):
    """Simple ping endpoint to test rate limiting"""
    try:
        client_ip = rate_limit_middleware._get_client_ip(request)
        
        return JSONResponse(content={
            'message': 'Rate limiting is active',
            'client_ip': client_ip,
            'timestamp': time.time(),
            'environment': rate_limit_middleware.environment,
            'multiplier': rate_limit_middleware.multiplier
        })
        
    except Exception as e:
        return JSONResponse(
            content={'error': str(e)},
            status_code=500
        )

import time