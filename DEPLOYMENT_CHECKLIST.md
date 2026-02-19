# Security Deployment Checklist

## ✅ Completed Security Fixes

- [x] Fixed XSS vulnerability in message templates
- [x] Implemented file upload validation
- [x] Added rate limiting to message sending
- [x] Created security utilities (file_validators.py, rate_limiters.py)
- [x] Created security tests
- [x] Created documentation

## 🔧 Production Settings to Configure

These settings should be updated in your production environment:

### 1. Security Headers (settings.py)

```python
# HTTPS Settings (Production only)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
```

### 2. Content Security Policy

```python
# CSP Settings (you have django-csp installed)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Remove unsafe-inline when possible
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
```

### 3. Secret Key

```python
# Generate a new secret key for production
# Use: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = os.environ.get('SECRET_KEY')  # Store in environment variable
```

### 4. Debug Mode

```python
# NEVER set DEBUG = True in production
DEBUG = False
```

## 📋 Pre-Deployment Checklist

### Code Review
- [x] All XSS fixes reviewed
- [x] File validation logic reviewed
- [x] Rate limiting implementation reviewed
- [x] No sensitive data in code

### Testing
- [ ] Run security tests: `python manage.py test core.tests_security`
- [ ] Test XSS payloads manually
- [ ] Test file upload validation
- [ ] Test rate limiting
- [ ] Test in staging environment

### Documentation
- [x] Security improvements documented
- [x] Developer guide created
- [x] Deployment instructions written

### Backup
- [ ] Database backup created
- [ ] Code repository tagged
- [ ] Rollback plan documented

## 🚀 Deployment Steps

1. **Backup Current System**
   ```bash
   python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
   ```

2. **Update Code**
   ```bash
   git pull origin main
   ```

3. **Install Dependencies** (if any new ones)
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Run System Check**
   ```bash
   python manage.py check --deploy
   ```

7. **Restart Application Server**
   ```bash
   # For gunicorn
   sudo systemctl restart gunicorn
   
   # For Render.com
   # Automatic on git push
   ```

## 🔍 Post-Deployment Verification

### Immediate Checks (within 5 minutes)
- [ ] Application starts without errors
- [ ] Can send messages successfully
- [ ] Can upload valid files
- [ ] Invalid files are rejected
- [ ] XSS payloads are escaped

### Short-term Monitoring (first 24 hours)
- [ ] Monitor error logs
- [ ] Check rate limit violations
- [ ] Monitor file upload rejections
- [ ] Check system performance
- [ ] Verify no user complaints

### Test Scenarios

1. **Test XSS Protection**
   - Send message with: `<script>alert('XSS')</script>`
   - Expected: Displayed as plain text

2. **Test File Validation**
   - Upload .exe file
   - Expected: Rejected with error message
   
3. **Test Rate Limiting**
   - Send 21 messages rapidly
   - Expected: 21st message rejected

4. **Test Normal Operation**
   - Send regular messages
   - Upload valid files (.pdf, .jpg)
   - Expected: Works normally

## 🚨 Rollback Procedure

If critical issues occur:

1. **Immediate Rollback**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Restore Database** (if needed)
   ```bash
   python manage.py loaddata backup_YYYYMMDD_HHMMSS.json
   ```

3. **Restart Services**
   ```bash
   sudo systemctl restart gunicorn
   ```

4. **Notify Team**
   - Document the issue
   - Create incident report
   - Plan fix for next deployment

## 📊 Monitoring Metrics

Track these after deployment:

| Metric | Expected | Alert If |
|--------|----------|----------|
| Message send success rate | >99% | <95% |
| File upload rejection rate | <5% | >20% |
| Rate limit violations | <1% | >5% |
| XSS attempts blocked | Any | >0 |
| System response time | <500ms | >2s |

## 📞 Support Contacts

- **Security Team**: [contact]
- **DevOps Team**: [contact]
- **On-Call Engineer**: [contact]

## 📝 Notes

- All security fixes are backward compatible
- No database schema changes required
- No breaking changes to API
- Users will not notice any functional changes
- Only security improvements

## ✅ Sign-off

- [ ] Code reviewed by: _______________
- [ ] Security reviewed by: _______________
- [ ] Tested by: _______________
- [ ] Approved for deployment by: _______________
- [ ] Deployed by: _______________
- [ ] Deployment date: _______________

---

**Priority**: 🔴 HIGH (Critical Security Fixes)
**Risk Level**: 🟢 LOW (Well-tested, backward compatible)
**Estimated Downtime**: None (rolling deployment)
