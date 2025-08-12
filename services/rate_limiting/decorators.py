#!/usr/bin/env python3
"""
Rate Limiting Decorators
Decorators for applying rate limits to FastAPI endpoints
"""

import logging
from functools import wraps
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from .middleware import rate_limit_middleware
from .config import RATE_LIMIT_HEADERS

logger = logging.getLogger(__name__)

def rate_limit(endpoint: str, require_auth: bool = False):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Args:
        endpoint: Endpoint identifier from RATE_LIMIT_CONFIG
        require_auth: Whether this endpoint requires authentication
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            user_id = None
            
            # Find request object in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if not request:
                logger.warning(f"No Request object found for rate limiting on {endpoint}")
                return await func(*args, **kwargs)
            
            # Get user ID if authentication is required or available
            if require_auth or 'user_id' in kwargs:
                try:
                    # Try to get user_id from kwargs first
                    if 'user_id' in kwargs:
                        user_id = kwargs['user_id']
                    else:
                        # Try to extract from authorization header
                        auth_header = request.headers.get('authorization')
                        if auth_header:
                            user_id = await _extract_user_from_token(auth_header)
                except Exception as e:
                    if require_auth:
                        logger.warning(f"Authentication required but failed for {endpoint}: {e}")
                        raise HTTPException(status_code=401, detail="Authentication required")
                    # If auth is optional, continue without user_id
                    pass
            
            # Check rate limits
            try:
                rate_check = await rate_limit_middleware.check_rate_limit(request, endpoint, user_id)
                
                if not rate_check['allowed']:
                    # Create rate limit exceeded response
                    headers = _create_rate_limit_headers(rate_check)
                    
                    error_detail = _create_error_message(rate_check)
                    
                    raise HTTPException(
                        status_code=429,
                        detail=error_detail,
                        headers=headers
                    )
                
                # Execute the original function
                response = await func(*args, **kwargs)
                
                # Add rate limit headers to successful responses if it's a JSONResponse
                if isinstance(response, JSONResponse) and 'limit' in rate_check:
                    headers = _create_rate_limit_headers(rate_check)
                    for key, value in headers.items():
                        response.headers[key] = value
                
                return response
                
            except HTTPException:
                # Re-raise HTTP exceptions (like 429)
                raise
            except Exception as e:
                logger.error(f"Error in rate limiting for {endpoint}: {e}")
                # On error, allow the request to proceed but log the issue
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def _create_rate_limit_headers(rate_check: Dict[str, Any]) -> Dict[str, str]:
    """Create rate limit headers for response"""
    headers = {}
    
    if 'limit' in rate_check:
        headers[RATE_LIMIT_HEADERS['limit_header']] = str(rate_check['limit'])
    
    if 'remaining' in rate_check:
        headers[RATE_LIMIT_HEADERS['remaining_header']] = str(rate_check['remaining'])
    
    if 'reset_time' in rate_check:
        headers[RATE_LIMIT_HEADERS['reset_header']] = str(rate_check['reset_time'])
    
    if 'retry_after' in rate_check:
        headers[RATE_LIMIT_HEADERS['retry_after_header']] = str(rate_check['retry_after'])
    
    return headers

def _create_error_message(rate_check: Dict[str, Any]) -> str:
    """Create user-friendly error message based on rate check result"""
    reason = rate_check.get('reason', 'unknown')
    
    if reason == 'ip_blocked':
        return "Your IP address has been temporarily blocked due to excessive requests. Please try again later."
    elif reason == 'burst_limit_exceeded':
        return "Too many requests in a short time. Please slow down and try again in a few seconds."
    elif reason == 'ip_rate_limit':
        return f"IP rate limit exceeded. Please try again in {rate_check.get('retry_after', 60)} seconds."
    elif reason == 'user_rate_limit':
        return f"User rate limit exceeded. Please try again in {rate_check.get('retry_after', 60)} seconds."
    else:
        return "Rate limit exceeded. Please try again later."

async def _extract_user_from_token(auth_header: str) -> Optional[str]:
    """Extract user ID from JWT token"""
    try:
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ", 1)[1]
        
        # Import here to avoid circular imports
        from jose import jwt
        import os
        
        JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey123")
        JWT_ALGORITHM = "HS256"
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
        
    except Exception as e:
        logger.warning(f"Error extracting user from token: {e}")
        return None

# Convenience decorators for common endpoint types
def auth_rate_limit(endpoint: str):
    """Rate limit decorator for authentication endpoints"""
    return rate_limit(endpoint, require_auth=False)

def protected_rate_limit(endpoint: str):
    """Rate limit decorator for protected endpoints that require authentication"""
    return rate_limit(endpoint, require_auth=True)

def public_rate_limit(endpoint: str):
    """Rate limit decorator for public endpoints"""
    return rate_limit(endpoint, require_auth=False)