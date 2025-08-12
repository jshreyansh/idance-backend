#!/usr/bin/env python3
"""
Rate Limiting Configuration
Defines rate limits for different endpoint tiers to protect against DDoS and abuse
"""

# Rate limit configurations for different endpoint tiers
RATE_LIMIT_CONFIG = {
    # TIER 1: Authentication (Strictest - Critical Security)
    'auth_login': {'ip': '5/minute', 'user': None},
    'auth_signup': {'ip': '3/minute', 'user': None},
    'auth_google': {'ip': '5/minute', 'user': None},
    'auth_verify_otp': {'ip': '3/minute', 'user': None},
    'auth_reset_password': {'ip': '3/hour', 'user': None},
    
    # TIER 2: File Uploads (High Impact - Resource Intensive)
    'upload_video': {'ip': '50/hour', 'user': '10/hour'},
    'upload_thumbnail': {'ip': '100/hour', 'user': '20/hour'},
    'upload_avatar': {'ip': '30/hour', 'user': '5/hour'},
    
    # TIER 3: AI Processing (High Impact - CPU Intensive)
    'ai_dance_breakdown': {'ip': '100/hour', 'user': '15/hour'},
    'ai_pose_analysis': {'ip': '200/hour', 'user': '30/hour'},
    'ai_video_analysis': {'ip': '150/hour', 'user': '25/hour'},
    
    # TIER 4: Challenge System (Moderate)
    'challenge_submit': {'ip': '100/hour', 'user': '20/hour'},
    'challenge_create': {'ip': '10/hour', 'user': '5/hour'},
    'challenge_vote': {'ip': '500/hour', 'user': '100/hour'},
    
    # TIER 5: Session Management (Standard)
    'session_start': {'ip': '200/hour', 'user': '50/hour'},
    'session_complete': {'ip': '200/hour', 'user': '50/hour'},
    'session_update': {'ip': '500/hour', 'user': '100/hour'},
    
    # TIER 6: Data Operations (Standard)
    'profile_update': {'ip': '100/hour', 'user': '30/hour'},
    'user_stats': {'ip': '500/hour', 'user': '100/hour'},
    
    # TIER 7: Data Retrieval (Loose)
    'feed_get': {'ip': '1000/minute', 'user': '200/minute'},
    'challenges_list': {'ip': '500/minute', 'user': '100/minute'},
    'user_profile': {'ip': '1000/minute', 'user': '200/minute'},
    'sessions_list': {'ip': '500/minute', 'user': '100/minute'},
    
    # TIER 8: Public Endpoints (Very Loose)
    'health_check': {'ip': '2000/minute', 'user': None},
    'public_data': {'ip': '5000/minute', 'user': None},
}

# DDoS Protection Configuration
DDOS_PROTECTION = {
    # Burst protection - short term limits
    'burst_limit': {'requests': 20, 'window': 10},  # 20 requests in 10 seconds
    'sustained_limit': {'requests': 100, 'window': 60},  # 100 requests in 1 minute
    
    # IP blocking thresholds
    'ip_block_threshold': 100,  # Block IP after 100 violations in window
    'block_duration': 3600,  # Block for 1 hour (3600 seconds)
    'violation_window': 3600,  # Track violations for 1 hour
    
    # Progressive penalties
    'progressive_blocks': {
        'first_offense': 300,   # 5 minutes
        'second_offense': 900,  # 15 minutes
        'third_offense': 3600,  # 1 hour
        'repeat_offender': 86400,  # 24 hours
    }
}

# Redis Configuration
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30,
}

# Rate limit response headers
RATE_LIMIT_HEADERS = {
    'limit_header': 'X-RateLimit-Limit',
    'remaining_header': 'X-RateLimit-Remaining', 
    'reset_header': 'X-RateLimit-Reset',
    'retry_after_header': 'Retry-After',
}

# Monitoring and alerting thresholds
MONITORING_CONFIG = {
    'high_violation_rate': {'threshold': 100, 'window': 3600},  # 100 violations per hour
    'ddos_detection': {'threshold': 1000, 'window': 60},  # 1000 requests per minute
    'user_abuse': {'threshold': 50, 'window': 3600},  # 50 violations per hour per user
    'suspicious_ip': {'threshold': 200, 'window': 3600},  # 200 violations per hour per IP
}

# Whitelist for trusted IPs (internal services, monitoring, etc.)
WHITELIST_IPS = [
    '127.0.0.1',
    '::1',
    'localhost',
    # Add your monitoring/internal IPs here
]

# Environment-specific multipliers
ENVIRONMENT_MULTIPLIERS = {
    'development': 10.0,  # Very loose limits for development
    'test': 5.0,          # Moderate limits for testing
    'production': 1.0,    # Strict limits for production
}