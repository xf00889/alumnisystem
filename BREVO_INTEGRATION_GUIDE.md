# Brevo Email Integration Guide

This guide explains how to configure and use Brevo email service alongside the existing SMTP configuration in the NORSU Alumni System.

## Overview

The system now supports two email providers:
- **SMTP**: Traditional SMTP email sending (existing functionality)
- **Brevo API**: Modern email service via Brevo API (new functionality)

## Features

### 1. Dual Provider Support
- Switch between SMTP and Brevo providers
- Automatic fallback to SMTP if Brevo is not configured
- Provider-specific configuration management

### 2. Brevo Configuration
- Store Brevo API credentials securely
- Test Brevo API connection
- Send test emails via Brevo
- Admin interface for configuration management

### 3. Email Provider Management
- Select active email provider
- Track usage statistics
- Monitor provider health
- Switch providers without code changes

## Setup Instructions

### 1. Database Migration
The required database tables have been created. If you need to run migrations manually:

```bash
python manage.py migrate core
```

### 2. Initialize Email Providers
Run the initialization command to create default provider entries:

```bash
python manage.py init_email_providers
```

### 3. Configure Brevo

#### Option A: Via Django Admin
1. Go to Django Admin → Core → Brevo Configurations
2. Click "Add Brevo Configuration"
3. Fill in the required fields:
   - **Name**: Descriptive name (e.g., "Brevo Production")
   - **API Key**: Your Brevo API key from account settings
   - **API URL**: `https://api.brevo.com/v3/smtp/email` (default)
   - **From Email**: Verified sender email address
   - **From Name**: Sender name (optional)
4. Save the configuration
5. Test the connection using admin actions

#### Option B: Via Django Settings
Add these settings to your `settings.py`:

```python
# Brevo Configuration (fallback if no database config)
BREVO_API_KEY = 'your_brevo_api_key_here'
BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'
BREVO_FROM_EMAIL = 'noreply@yourdomain.com'
BREVO_FROM_NAME = 'NORSU Alumni System'
```

### 4. Activate Brevo Provider
1. Go to Django Admin → Core → Email Providers
2. Find the "Brevo API" provider
3. Click "Activate Provider" action
4. This will deactivate the SMTP provider and activate Brevo

## Usage

### Sending Emails

The system automatically uses the active provider. No code changes are needed for existing email functionality.

#### Using the Unified Email Function
```python
from core.email_utils import send_email_with_provider

# Send email using active provider
send_email_with_provider(
    subject='Test Email',
    message='This is a test email',
    recipient_list=['user@example.com'],
    html_message='<h1>Test Email</h1>'
)

# Send email using specific provider
send_email_with_provider(
    subject='Test Email',
    message='This is a test email',
    recipient_list=['user@example.com'],
    provider_type='brevo'  # or 'smtp'
)
```

#### Using Legacy Functions (Still Supported)
```python
from core.email_utils import send_email_with_smtp_config

# This still works and uses the active provider
send_email_with_smtp_config(
    subject='Test Email',
    message='This is a test email',
    recipient_list=['user@example.com']
)
```

### Checking Current Configuration
```python
from core.email_utils import get_current_email_info

info = get_current_email_info()
print(f"Current provider: {info['provider']}")
print(f"Configuration: {info}")
```

## Brevo API Setup

### 1. Create Brevo Account
1. Go to [Brevo](https://www.brevo.com/)
2. Sign up for a free account
3. Verify your email address

### 2. Get API Key
1. Log into your Brevo account
2. Go to Settings → SMTP & API
3. Under "API keys" tab, click "Generate a new API key"
4. Name your API key (e.g., "NORSU Alumni System")
5. Copy the generated API key

### 3. Verify Sender Domain
1. Go to Settings → Senders & Domains
2. Add and verify your domain
3. Or use a verified sender email address

## Admin Interface

### Brevo Configuration Management
- **List View**: See all Brevo configurations with status
- **Test Actions**: Test API connection and send test emails
- **Configuration**: Manage API keys and settings
- **Status Tracking**: Monitor verification status and test results

### Email Provider Management
- **Provider Selection**: Activate/deactivate providers
- **Usage Statistics**: Track emails sent per provider
- **Health Monitoring**: View last errors and usage
- **Quick Actions**: Switch providers with one click

## Testing

### Test Brevo Integration
Run the provided test script:

```bash
python test_brevo_integration.py
```

This will:
- Create a test Brevo configuration
- Test provider selection
- Test email sending with both providers
- Clean up test data

### Manual Testing
1. Create a Brevo configuration in admin
2. Test the connection using admin actions
3. Send a test email
4. Switch to Brevo provider
5. Send another test email

## Troubleshooting

### Common Issues

#### 1. "API key is not configured"
- Ensure you have a Brevo configuration in the database
- Check that the configuration is active and verified
- Verify the API key is correct

#### 2. "Key not found" (401 error)
- Check your Brevo API key
- Ensure the API key is valid and not expired
- Verify you're using the correct API endpoint

#### 3. "Sender not verified"
- Verify your sender email address in Brevo
- Check domain authentication in Brevo settings
- Use a verified sender email address

#### 4. Provider not switching
- Check that only one provider is active at a time
- Ensure the target provider has a valid configuration
- Check for database constraints

### Debug Information
```python
from core.email_utils import get_current_email_info
from core.models.email_provider import EmailProvider

# Check current email configuration
print(get_current_email_info())

# Check all providers
for provider in EmailProvider.objects.all():
    print(f"{provider.provider_type}: {provider.is_active} - {provider.is_configured()}")
```

## Migration from SMTP

### Gradual Migration
1. Keep SMTP as active provider initially
2. Configure and test Brevo
3. Switch to Brevo when ready
4. Monitor email delivery
5. Keep SMTP as backup if needed

### Complete Migration
1. Configure Brevo with all required settings
2. Test thoroughly in staging environment
3. Switch to Brevo in production
4. Monitor for any issues
5. Remove SMTP configuration if desired

## Security Considerations

### API Key Security
- Store API keys in database (encrypted in production)
- Use environment variables for sensitive data
- Rotate API keys regularly
- Monitor API key usage

### Email Security
- Use verified sender addresses
- Implement rate limiting
- Monitor for abuse
- Use HTTPS for all API calls

## Performance

### Brevo Advantages
- Better deliverability rates
- Detailed analytics and tracking
- Higher sending limits
- Professional email templates

### SMTP Advantages
- Lower cost for high volume
- Full control over email server
- No API rate limits
- Simpler debugging

## Support

For issues with:
- **Brevo API**: Check [Brevo Documentation](https://developers.brevo.com/docs/getting-started)
- **System Integration**: Check Django logs and admin interface
- **Email Delivery**: Use Brevo dashboard for delivery reports

## Files Modified/Created

### New Files
- `core/models/brevo_config.py` - Brevo configuration model
- `core/models/email_provider.py` - Email provider management
- `core/brevo_email.py` - Brevo email utilities
- `core/management/commands/init_email_providers.py` - Initialization command
- `test_brevo_integration.py` - Test script

### Modified Files
- `core/email_utils.py` - Added unified email sending
- `core/admin.py` - Added admin interfaces
- `core/models/__init__.py` - Added new models
- `accounts/security_views.py` - Updated to use unified email function

### Database Changes
- New table: `core_brevoconfig`
- New table: `core_emailprovider`
- Migration: `core/migrations/0012_brevoconfig_emailprovider.py`
