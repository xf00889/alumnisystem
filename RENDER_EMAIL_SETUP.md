# Email Setup for Render Deployment

## Issue
Emails are working on localhost but not on Render production server.

## Root Cause
The Django settings were configured to use `console.EmailBackend` which only prints emails to console instead of actually sending them.

## Solution

### 1. Environment Variables on Render
You need to set these environment variables in your Render dashboard:

1. Go to your Render dashboard
2. Navigate to your web service
3. Go to "Environment" tab
4. Add these environment variables:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-gmail-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-gmail-email@gmail.com
DEBUG=False
```

### 2. Gmail App Password Setup
Since you're using Gmail, you need to:

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use this password (not your regular Gmail password) for `EMAIL_HOST_PASSWORD`

### 3. Test Email Configuration
After setting up the environment variables, you can test the email configuration by running:

```bash
python manage.py test_production_email --email your-test-email@gmail.com
```

### 4. Check Logs
If emails still don't work, check the Render logs for any error messages. The system now logs email sending attempts.

## Changes Made

1. **Fixed Email Backend**: Changed from console backend to SMTP backend for production
2. **Added Environment Detection**: Uses console backend for DEBUG=True, SMTP for production
3. **Added Email Testing Command**: `test_production_email` command to verify configuration
4. **Enhanced Logging**: Added more detailed logging for email sending attempts

## Verification Steps

1. Set the environment variables on Render
2. Deploy the updated code
3. Test email sending using the management command
4. Try making a donation on the live site
5. Check your email for the confirmation

## Troubleshooting

If emails still don't work:

1. Check Render logs for error messages
2. Verify environment variables are set correctly
3. Test with the management command
4. Ensure Gmail app password is correct
5. Check if Render has any email restrictions

## Security Note

Never commit email passwords to your code repository. Always use environment variables for sensitive information like email credentials.
