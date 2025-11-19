# Rate Limiting Implementation

## Overview
This document describes the rate limiting implementation for the documentation search feature.

## Requirements
- **5.1**: Limit search requests to 30 per minute per IP address
- **5.2**: Return HTTP 429 status when rate limit is exceeded
- **5.3**: Apply per-user rate limiting for authenticated users

## Implementation Details

### 1. Settings Configuration
**File**: `norsu_alumni/settings.py`

Added rate limiting configuration:
```python
# Rate Limiting Settings
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
```

### 2. View Decorator Application
**File**: `docs/views.py`

Applied rate limiting decorators to `DocumentationSearchView`:
- IP-based limit: 30 requests per minute
- User-based limit: 60 requests per minute

```python
@method_decorator(ratelimit(key='ip', rate='30/m', method='GET'))
@method_decorator(ratelimit(key='user', rate='60/m', method='GET'))
def dispatch(self, request, *args, **kwargs):
    # Check if rate limit was exceeded
    if getattr(request, 'limited', False):
        # Return HTTP 429 with Retry-After header
        ...
```

### 3. Custom Error Handling
When rate limit is exceeded:
- Returns HTTP 429 status code
- Includes `Retry-After: 60` header
- Logs the rate limit violation with error ID
- Provides user-friendly error message

### 4. Dependencies
- `django-ratelimit==4.1.0` (already in requirements.txt)

## Testing
Rate limiting tests will be implemented in task 7.3 (`docs/tests/test_rate_limiting.py`).

To manually test:
1. Start the development server
2. Login as an admin user
3. Navigate to `/docs/search/?q=test`
4. Refresh the page 31 times rapidly
5. The 31st request should return HTTP 429 with "Rate limit exceeded" message

## Security Benefits
- Prevents DoS attacks on search endpoint
- Protects server resources from abuse
- Provides graceful degradation under high load
- Logs suspicious activity for monitoring

## Configuration
Rate limiting can be disabled by setting `RATELIMIT_ENABLE = False` in settings.py.

The cache backend used for rate limiting is configured via `RATELIMIT_USE_CACHE = 'default'`.
