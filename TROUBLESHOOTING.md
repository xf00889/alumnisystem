# NORSU Alumni System - Render Troubleshooting Guide

## Common Deployment Issues

### 1. Build Failures

#### Issue: "Requirements installation failed"
**Symptoms:**
- Build fails during `pip install -r requirements.txt`
- Missing package errors

**Solutions:**
```bash
# Check requirements.txt format
# Ensure no Windows line endings (CRLF)
# Verify all package versions are available

# Fix line endings (if needed):
sed -i 's/\r$//' requirements.txt

# Test locally:
pip install -r requirements.txt
```

#### Issue: "Python version mismatch"
**Symptoms:**
- Build fails with Python version errors
- Package compatibility issues

**Solutions:**
1. Add `runtime.txt` file:
   ```
   python-3.11.0
   ```
2. Or set environment variable:
   ```
   PYTHON_VERSION=3.11.0
   ```

### 2. Database Connection Issues

#### Issue: "Database connection failed"
**Symptoms:**
- `django.db.utils.OperationalError`
- Connection timeout errors

**Solutions:**
1. **Check DATABASE_URL format:**
   ```
   postgresql://username:password@hostname:port/database_name
   ```

2. **Verify database is created and running:**
   - Go to Render dashboard
   - Check PostgreSQL service status
   - Ensure database is in same region as web service

3. **Test connection manually:**
   ```bash
   # In Render shell
   python manage.py dbshell
   ```

#### Issue: "Migration failures"
**Symptoms:**
- Migrations fail during deployment
- Table already exists errors

**Solutions:**
```bash
# Reset migrations (if safe to do so)
python manage.py migrate --fake-initial

# Or run specific migration
python manage.py migrate app_name migration_name

# Check migration status
python manage.py showmigrations
```

### 3. Static Files Issues

#### Issue: "Static files not loading"
**Symptoms:**
- CSS/JS files return 404
- Admin panel styling broken

**Solutions:**
1. **Verify whitenoise configuration:**
   ```python
   # In settings.py
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be here
       # ... other middleware
   ]
   
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

2. **Run collectstatic manually:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Check static files settings:**
   ```python
   STATIC_URL = '/static/'
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
   ```

### 4. Environment Variables

#### Issue: "Environment variable not found"
**Symptoms:**
- `KeyError` for missing environment variables
- Default values not working

**Solutions:**
1. **Check variable names in Render dashboard:**
   - No typos in variable names
   - Values are properly set
   - No extra spaces

2. **Use proper defaults:**
   ```python
   from decouple import config
   
   DEBUG = config('DEBUG', default=False, cast=bool)
   SECRET_KEY = config('SECRET_KEY', default='fallback-key')
   ```

3. **Verify in Render shell:**
   ```bash
   echo $DEBUG
   echo $SECRET_KEY
   ```

### 5. ALLOWED_HOSTS Issues

#### Issue: "DisallowedHost error"
**Symptoms:**
- 400 Bad Request errors
- "Invalid HTTP_HOST header" messages

**Solutions:**
1. **Add Render domain to ALLOWED_HOSTS:**
   ```python
   ALLOWED_HOSTS = ['your-app-name.onrender.com', 'localhost', '127.0.0.1']
   ```

2. **Use environment variable:**
   ```python
   RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default=None)
   if RENDER_EXTERNAL_HOSTNAME:
       ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
   ```

### 6. CSRF Issues

#### Issue: "CSRF verification failed"
**Symptoms:**
- Forms return CSRF errors
- 403 Forbidden on form submissions

**Solutions:**
1. **Add domain to CSRF_TRUSTED_ORIGINS:**
   ```python
   CSRF_TRUSTED_ORIGINS = [
       'https://your-app-name.onrender.com',
       'http://localhost:8000',
   ]
   ```

2. **Check HTTPS settings:**
   ```python
   # For production
   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True
   ```

### 7. Memory and Performance Issues

#### Issue: "Application running slowly"
**Symptoms:**
- Long response times
- Timeout errors
- Memory warnings

**Solutions:**
1. **Optimize database queries:**
   ```python
   # Use select_related and prefetch_related
   queryset = Model.objects.select_related('foreign_key')
   ```

2. **Enable caching:**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
       }
   }
   ```

3. **Monitor resource usage:**
   - Check Render metrics dashboard
   - Consider upgrading plan if needed

### 8. WebSocket/Channels Issues

#### Issue: "WebSocket connection failed"
**Symptoms:**
- Real-time features not working
- WebSocket connection errors

**Solutions:**
1. **Verify Redis configuration:**
   ```python
   REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379')
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               "hosts": [REDIS_URL],
           },
       },
   }
   ```

2. **Check if Redis service is running:**
   - Ensure Redis service is created in Render
   - Verify connection string

3. **Temporarily disable WebSockets:**
   ```python
   # In asgi.py - comment out WebSocket routing
   # "websocket": URLRouter([]),
   ```

## Debugging Tools

### 1. Render Shell Access
```bash
# Access your application shell
python manage.py shell

# Run Django commands
python manage.py check
python manage.py migrate --plan
python manage.py collectstatic --dry-run
```

### 2. Log Analysis
```bash
# View recent logs
tail -f /var/log/render.log

# Search for specific errors
grep "ERROR" /var/log/render.log
```

### 3. Health Check Endpoint
Add a health check view:
```python
# views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "connected"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
```

## Performance Optimization

### 1. Database Optimization
```python
# Add database indexes
class Meta:
    indexes = [
        models.Index(fields=['created_at']),
        models.Index(fields=['user', 'created_at']),
    ]

# Use database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60
```

### 2. Static Files Optimization
```python
# Enable compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Set cache headers
WHITENOISE_MAX_AGE = 31536000  # 1 year
```

### 3. Caching Strategy
```python
# Cache expensive operations
from django.core.cache import cache

def expensive_operation():
    result = cache.get('expensive_key')
    if result is None:
        result = perform_calculation()
        cache.set('expensive_key', result, 300)  # 5 minutes
    return result
```

## Emergency Procedures

### 1. Rollback Deployment
1. Go to Render dashboard
2. Click on your service
3. Go to "Deploys" tab
4. Click "Redeploy" on previous working version

### 2. Database Recovery
```bash
# Create database backup
pg_dump $DATABASE_URL > backup.sql

# Restore from backup
psql $DATABASE_URL < backup.sql
```

### 3. Emergency Maintenance Mode
```python
# Quick maintenance page
# Create maintenance.html template
# Add middleware to show maintenance page

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if config('MAINTENANCE_MODE', default=False, cast=bool):
            return render(request, 'maintenance.html', status=503)
        return self.get_response(request)
```

## Getting Help

### 1. Check Logs First
- Render dashboard → Your service → Logs
- Look for error messages and stack traces

### 2. Common Log Locations
- Build logs: During deployment
- Runtime logs: Application errors
- Database logs: Connection and query issues

### 3. Support Resources
- [Render Documentation](https://render.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Community Forums](https://community.render.com)

### 4. When to Contact Support
- Platform-specific issues
- Billing questions
- Service outages
- Account problems

---

**Remember:** Always test changes in a staging environment before deploying to production!
