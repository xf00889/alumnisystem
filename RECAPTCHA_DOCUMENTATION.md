# reCAPTCHA Implementation Documentation

## Overview

This document provides comprehensive documentation for the Google reCAPTCHA v3 implementation in the NORSU Alumni System. The implementation provides spam protection across all critical user interaction points while maintaining a seamless user experience.

## Table of Contents

1. [Architecture](#architecture)
2. [Configuration](#configuration)
3. [Forms Integration](#forms-integration)
4. [Monitoring & Analytics](#monitoring--analytics)
5. [Admin Management](#admin-management)
6. [Security Features](#security-features)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

## Architecture

### Core Components

1. **reCAPTCHA Configuration Model** (`core.models.recaptcha_config.ReCaptchaConfig`)
   - Stores reCAPTCHA site keys, secret keys, and configuration
   - Supports multiple configurations with activation status
   - Version and threshold settings

2. **Form Integration** (`accounts.forms`, `core.forms`, `events.forms`, `feedback.forms`)
   - Custom forms with integrated reCAPTCHA fields
   - Server-side validation and error handling
   - Consistent user experience across all forms

3. **Monitoring System** (`core.recaptcha_monitoring`)
   - Real-time logging of reCAPTCHA events
   - Performance metrics and analytics
   - Suspicious activity detection

4. **Admin Interface** (`core.recaptcha_admin_views`, `core.recaptcha_analytics_views`)
   - Configuration management
   - Analytics dashboard
   - Performance monitoring

### Data Flow

```
User Form Submission → reCAPTCHA Validation → Server Processing → Monitoring Logging → Response
```

## Configuration

### Django Settings

```python
# reCAPTCHA Settings
RECAPTCHA_PUBLIC_KEY = '6Le7kesrAAAAAAyjoHeSENUJf9MpmKUdrT7JjbOg'
RECAPTCHA_PRIVATE_KEY = '6Le7kesrAAAAAKldE5dZ2n4_Hwe1n7wmnginjNmD'
RECAPTCHA_REQUIRED_SCORE = 0.5  # For reCAPTCHA v3
RECAPTCHA_DOMAIN = 'www.google.com'  # Use www.recaptcha.net for China

# Django Allauth Custom Forms
ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm',
    'signup': 'accounts.forms.CustomSignupForm',
}

# Logging Configuration
LOGGING = {
    'loggers': {
        'django_recaptcha': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'recaptcha': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

### Base Template Integration

```html
<!-- Google reCAPTCHA v3 -->
<script src="https://www.google.com/recaptcha/api.js?render={{ RECAPTCHA_PUBLIC_KEY|default:'6Le7kesrAAAAAAyjoHeSENUJf9MpmKUdrT7JjbOg' }}"></script>
```

## Forms Integration

### Protected Forms

The following forms are protected with reCAPTCHA:

1. **User Registration** (`accounts.forms.CustomSignupForm`)
2. **User Login** (`accounts.forms.CustomLoginForm`)
3. **Contact Us** (`core.forms.ContactForm`)
4. **Password Reset Email** (`accounts.forms.PasswordResetEmailForm`)
5. **Password Reset OTP** (`accounts.forms.PasswordResetOTPForm`)
6. **Password Reset New Password** (`accounts.forms.PasswordResetNewPasswordForm`)
7. **Public Event Creation** (`events.forms.PublicEventForm`)
8. **Feedback Submission** (`feedback.forms.FeedbackForm`)

### Form Implementation Pattern

```python
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

class CustomForm(forms.Form):
    # ... other fields ...
    
    # reCAPTCHA field for spam protection
    captcha = ReCaptchaField(
        widget=ReCaptchaV3(
            attrs={
                'data-callback': 'onRecaptchaSuccess',
                'data-expired-callback': 'onRecaptchaExpired',
                'data-error-callback': 'onRecaptchaError',
            }
        ),
        label='Security Verification'
    )
```

### Template Integration

```html
<!-- reCAPTCHA Section -->
<div class="form-group">
    <label class="form-label">{{ form.captcha.label }}</label>
    {{ form.captcha }}
    <small class="form-text text-muted">
        <i class="fas fa-shield-alt"></i> This helps us prevent spam and protect our system
    </small>
    {% if form.captcha.errors %}
        <div class="text-danger small mt-1">
            {% for error in form.captcha.errors %}{{ error }}{% endfor %}
        </div>
    {% endif %}
</div>
```

## Monitoring & Analytics

### Monitoring System

The monitoring system tracks:

- **Success/Failure Rates**: Overall and per-form statistics
- **Performance Metrics**: Response times and validation scores
- **Suspicious Activity**: High failure rates from specific IPs
- **Hourly Trends**: Activity patterns over time

### Analytics Dashboard

Access the analytics dashboard at: `/admin-dashboard/recaptcha/analytics/`

Features:
- Real-time metrics display
- Interactive charts and graphs
- Form-specific performance data
- Spam reduction statistics
- Data export capabilities

### Monitoring Integration

```python
from core.recaptcha_monitoring import log_recaptcha_success, log_recaptcha_failure, log_recaptcha_error

# In your view
if form.is_valid():
    user_ip = request.META.get('REMOTE_ADDR', 'unknown')
    log_recaptcha_success('form_name', user_ip)
    # Process form...
else:
    user_ip = request.META.get('REMOTE_ADDR', 'unknown')
    if 'captcha' in form.errors:
        log_recaptcha_failure('form_name', user_ip, 'Validation failed')
```

## Admin Management

### Configuration Management

Access reCAPTCHA configuration at: `/admin-dashboard/recaptcha/`

Features:
- Quick setup wizard
- Multiple configuration support
- Activation/deactivation
- Testing capabilities

### Quick Setup

1. Navigate to **reCAPTCHA Configuration** in admin sidebar
2. Click **Quick Setup**
3. Enter your Google reCAPTCHA keys
4. Configure threshold and version
5. Activate the configuration

### Configuration Options

- **Site Key**: Public key from Google reCAPTCHA console
- **Secret Key**: Private key from Google reCAPTCHA console
- **Version**: reCAPTCHA version (v2 or v3)
- **Threshold**: Minimum score for v3 (0.0-1.0)
- **Domain**: Domain for reCAPTCHA service

## Security Features

### Protection Mechanisms

1. **Server-Side Validation**: All reCAPTCHA tokens validated server-side
2. **Score-Based Filtering**: reCAPTCHA v3 uses behavioral analysis
3. **Rate Limiting**: Built-in protection against abuse
4. **IP Monitoring**: Suspicious activity detection
5. **CSRF Protection**: Maintained alongside reCAPTCHA

### Security Best Practices

- **Key Management**: Store secret keys securely
- **Score Thresholds**: Adjust based on your risk tolerance
- **Monitoring**: Regular review of analytics data
- **Updates**: Keep reCAPTCHA library updated

### Threat Mitigation

- **Bot Protection**: Prevents automated form submissions
- **Spam Reduction**: Blocks malicious content
- **Account Security**: Protects against brute force attacks
- **Data Integrity**: Ensures legitimate user interactions

## Troubleshooting

### Common Issues

#### reCAPTCHA Not Loading

**Symptoms**: reCAPTCHA widget not visible, JavaScript errors

**Solutions**:
1. Check site key configuration
2. Verify domain settings in Google console
3. Check network connectivity
4. Review browser console for errors

#### Validation Failures

**Symptoms**: Forms rejected with reCAPTCHA errors

**Solutions**:
1. Verify secret key configuration
2. Check score threshold settings
3. Review server logs for details
4. Test with different browsers

#### Performance Issues

**Symptoms**: Slow page loading, form submission delays

**Solutions**:
1. Optimize reCAPTCHA loading
2. Check network latency
3. Review server performance
4. Consider caching strategies

### Debug Mode

Enable debug logging:

```python
LOGGING = {
    'loggers': {
        'django_recaptcha': {
            'level': 'DEBUG',
        },
        'recaptcha': {
            'level': 'DEBUG',
        },
    },
}
```

### Testing

Test reCAPTCHA functionality:

1. **Test Page**: `/test-recaptcha/`
2. **Admin Testing**: Use configuration test feature
3. **Form Testing**: Submit forms with/without reCAPTCHA
4. **Analytics**: Monitor success/failure rates

## API Reference

### Monitoring Functions

```python
# Log successful validation
log_recaptcha_success(form_name: str, user_ip: str, score: Optional[float] = None)

# Log failed validation
log_recaptcha_failure(form_name: str, user_ip: str, reason: str, score: Optional[float] = None)

# Log validation errors
log_recaptcha_error(form_name: str, user_ip: str, error: str)

# Get metrics
get_recaptcha_metrics() -> Dict[str, Any]

# Get success rate
get_recaptcha_success_rate() -> float

# Get spam reduction estimate
get_spam_reduction_estimate() -> Dict[str, Any]
```

### Admin URLs

- **Configuration List**: `/admin-dashboard/recaptcha/`
- **Quick Setup**: `/admin-dashboard/recaptcha/quick-setup/`
- **Analytics Dashboard**: `/admin-dashboard/recaptcha/analytics/`
- **Analytics API**: `/admin-dashboard/recaptcha/analytics/api/`

### Form Fields

```python
# reCAPTCHA field
captcha = ReCaptchaField(
    widget=ReCaptchaV3(
        attrs={
            'data-callback': 'onRecaptchaSuccess',
            'data-expired-callback': 'onRecaptchaExpired',
            'data-error-callback': 'onRecaptchaError',
        }
    ),
    label='Security Verification'
)
```

## Maintenance

### Regular Tasks

1. **Monitor Analytics**: Review weekly performance reports
2. **Update Keys**: Rotate keys as needed
3. **Review Logs**: Check for unusual activity
4. **Performance Tuning**: Adjust thresholds based on data

### Backup & Recovery

- **Configuration Backup**: Export reCAPTCHA settings
- **Analytics Data**: Regular data export
- **Key Rotation**: Maintain backup keys
- **Disaster Recovery**: Document recovery procedures

## Support

### Resources

- **Google reCAPTCHA Documentation**: https://developers.google.com/recaptcha
- **django-recaptcha Documentation**: https://github.com/torchbox/django-recaptcha
- **System Logs**: Check Django logs for detailed information
- **Analytics Dashboard**: Monitor real-time performance

### Contact

For technical support or questions about the reCAPTCHA implementation, contact the development team or refer to the system documentation.

---

**Last Updated**: October 16, 2025  
**Version**: 1.0  
**Status**: Production Ready
