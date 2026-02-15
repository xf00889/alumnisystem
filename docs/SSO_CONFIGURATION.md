# SSO Configuration Guide

## Overview

The NORSU Alumni System now supports database-backed SSO (Single Sign-On) configuration, allowing administrators to manage OAuth credentials through the admin interface instead of environment variables.

## Features

- **Database-backed configuration**: Store OAuth credentials securely in the database
- **Multiple providers**: Support for Google OAuth and Facebook OAuth
- **Admin interface**: Easy-to-use web interface for managing SSO settings
- **Configuration testing**: Test OAuth credentials before activating
- **Usage tracking**: Monitor login counts and last usage for each provider
- **Enable/disable providers**: Control which SSO options appear on the login page
- **Migration tool**: Migrate existing .env credentials to database

## Supported Providers

### Google OAuth
- Scopes: profile, email
- Trusted email verification
- Automatic profile picture download

### Facebook OAuth
- Scopes: email, public_profile
- Configurable email verification trust
- Profile data mapping

## Setup Instructions

### 1. Run Migrations

```bash
python manage.py migrate
```

### 2. Migrate Existing Configuration (Optional)

If you have existing SSO credentials in your `.env` file:

```bash
python manage.py migrate_sso_config
```

This will:
- Read OAuth credentials from environment variables
- Create database configurations
- Test the configurations
- Provide next steps

### 3. Access Admin Interface

1. Log in as an admin or superuser
2. Navigate to: **Admin Dashboard → SSO Configuration**
3. Or visit: `https://your-domain.com/admin-dashboard/sso/`

### 4. Add SSO Configuration

#### For Google OAuth:

1. Click "Add SSO Configuration"
2. Fill in the form:
   - **Name**: e.g., "Google Production"
   - **Provider**: Select "Google OAuth"
   - **Client ID**: Your Google OAuth Client ID
   - **Client Secret**: Your Google OAuth Client Secret
   - **Scopes**: `profile,email` (default)
   - **Trust Email Verification**: ✓ (recommended)
   - **Enabled**: ✓
   - **Set as Active**: ✓
3. Click "Save Configuration"
4. Click "Test" to verify the configuration

#### For Facebook OAuth:

1. Click "Add SSO Configuration"
2. Fill in the form:
   - **Name**: e.g., "Facebook Production"
   - **Provider**: Select "Facebook OAuth"
   - **Client ID**: Your Facebook App ID
   - **Client Secret**: Your Facebook App Secret
   - **Scopes**: `email,public_profile` (default)
   - **Trust Email Verification**: ✗ (optional)
   - **Enabled**: ✓
   - **Set as Active**: ✓
3. Click "Save Configuration"
4. Click "Test" to verify the configuration

## OAuth Provider Setup

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Configure OAuth consent screen
6. Add authorized redirect URI:
   ```
   https://your-domain.com/accounts/google/login/callback/
   ```
7. Copy Client ID and Client Secret
8. Add them to SSO Configuration in admin interface

### Facebook OAuth Setup

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or select existing one
3. Add **Facebook Login** product
4. In **Settings → Basic**, copy App ID and App Secret
5. In **Facebook Login → Settings**, add OAuth redirect URI:
   ```
   https://your-domain.com/accounts/facebook/login/callback/
   ```
6. Add App ID and App Secret to SSO Configuration in admin interface

## Configuration Management

### Activate Configuration

Only one configuration per provider can be active at a time:

1. Go to SSO Configuration list
2. Find the configuration you want to activate
3. Click the "Activate" button (✓)
4. The previous active configuration will be automatically deactivated

### Enable/Disable Provider

Control whether a provider appears on the login page:

1. Go to SSO Configuration list
2. Find the configuration
3. Click the "Enable/Disable" button (power icon)
4. Disabled providers won't show on the login page

### Test Configuration

Verify OAuth credentials are valid:

1. Go to SSO Configuration list
2. Find the configuration
3. Click the "Test" button (flask icon)
4. View test results

### Edit Configuration

Update OAuth credentials or settings:

1. Go to SSO Configuration list
2. Find the configuration
3. Click the "Edit" button (pencil icon)
4. Update fields
5. Click "Save Configuration"

### Delete Configuration

Remove an SSO configuration:

1. Go to SSO Configuration list
2. Find the configuration
3. Click the "Delete" button (trash icon)
4. Confirm deletion

## Usage Tracking

The system automatically tracks:
- **Login Count**: Number of successful logins using each configuration
- **Last Used**: Timestamp of the most recent login
- **Test Results**: Results from configuration tests
- **Last Tested**: Timestamp of the last test

View this information in the SSO Configuration list.

## Security Considerations

### Credential Storage

- OAuth credentials are stored encrypted in the database
- Client secrets are stored as password fields (not visible in plain text)
- Access restricted to admin users only

### Best Practices

1. **Use HTTPS**: Always use HTTPS in production
2. **Restrict Admin Access**: Limit who can access SSO configuration
3. **Regular Testing**: Test configurations periodically
4. **Monitor Usage**: Review login counts and last usage
5. **Rotate Credentials**: Update OAuth credentials periodically
6. **Disable Unused Providers**: Disable providers you're not using

## Troubleshooting

### "Invalid Client" Error

**Cause**: OAuth credentials are incorrect or misconfigured

**Solution**:
1. Verify Client ID and Client Secret are correct
2. Check that credentials match the provider console
3. Ensure OAuth redirect URIs are configured correctly
4. Test the configuration in admin interface

### "Access Denied" Error

**Cause**: User cancelled OAuth flow or permissions denied

**Solution**:
- This is normal user behavior, no action needed
- User can try again or use email/password login

### Provider Not Showing on Login Page

**Cause**: Configuration is disabled or not active

**Solution**:
1. Go to SSO Configuration list
2. Ensure configuration is **Enabled** (green badge)
3. Ensure configuration is **Active** (active badge)
4. Clear browser cache and try again

### "Configuration Not Found" Error

**Cause**: No active configuration for the provider

**Solution**:
1. Go to SSO Configuration list
2. Create a new configuration or activate existing one
3. Ensure "Set as Active" is checked

## Migration from .env

### Before Migration

Your `.env` file might have:
```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret
```

### After Migration

1. Run migration command:
   ```bash
   python manage.py migrate_sso_config
   ```

2. Verify configurations in admin interface

3. Test each configuration

4. (Optional) Remove credentials from `.env`:
   ```env
   # GOOGLE_CLIENT_ID=your-client-id  # Now in database
   # GOOGLE_CLIENT_SECRET=your-client-secret  # Now in database
   ```

### Rollback

If you need to rollback to `.env` configuration:

1. Add credentials back to `.env`
2. Delete database configurations
3. Restart the application

## API Reference

### Models

#### SSOConfig

**Fields**:
- `name`: Configuration name
- `provider`: Provider type (google, facebook)
- `client_id`: OAuth Client ID
- `secret_key`: OAuth Client Secret
- `scopes`: Comma-separated OAuth scopes
- `verified_email`: Trust email verification from provider
- `is_active`: Active configuration flag
- `enabled`: Provider enabled flag
- `is_verified`: Configuration tested flag
- `login_count`: Number of successful logins
- `last_used`: Last login timestamp
- `test_result`: Last test result message
- `last_tested`: Last test timestamp

**Methods**:
- `get_provider_config()`: Get django-allauth format configuration
- `test_configuration()`: Test OAuth credentials
- `increment_usage()`: Track login usage
- `get_active_providers()`: Get all active provider configurations
- `get_provider_config_by_type(provider_type)`: Get config for specific provider

### Utilities

#### core.sso_utils

**Functions**:
- `get_sso_providers_config()`: Get cached SSO configuration
- `clear_sso_cache()`: Clear SSO configuration cache
- `get_enabled_sso_providers()`: Get list of enabled provider names
- `is_sso_provider_enabled(provider_name)`: Check if provider is enabled
- `get_sso_provider_config(provider_name)`: Get configuration for provider

### Context Processors

#### core.context_processors.sso_context

Adds `enabled_sso_providers` to template context:
```python
{{ enabled_sso_providers }}  # ['google', 'facebook']
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review configuration in admin interface
3. Check application logs for detailed errors
4. Contact system administrator

## Changelog

### Version 1.0.0 (2024)
- Initial release
- Support for Google and Facebook OAuth
- Database-backed configuration
- Admin interface for management
- Configuration testing
- Usage tracking
- Migration tool from .env
