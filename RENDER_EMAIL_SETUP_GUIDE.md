# Render Email Setup Guide

## Problem
Render hosting has network restrictions that prevent direct SMTP connections to external email servers, causing "network unreachable" errors when trying to send emails.

## Solutions

### Option 1: Use SendGrid (Recommended)
SendGrid is a cloud-based email service that works well with Render.

#### Setup Steps:
1. **Create SendGrid Account**
   - Go to [sendgrid.com](https://sendgrid.com)
   - Sign up for a free account (100 emails/day free)

2. **Get API Key**
   - In SendGrid dashboard, go to Settings > API Keys
   - Create a new API key with "Full Access" permissions
   - Copy the API key

3. **Configure Render Environment Variables**
   - In your Render dashboard, go to your service
   - Go to Environment tab
   - Add: `SENDGRID_API_KEY=your_api_key_here`

4. **Install SendGrid Library**
   - Add to `requirements.txt`: `sendgrid==6.10.0`

5. **Verify Domain (Optional but Recommended)**
   - In SendGrid, go to Settings > Sender Authentication
   - Verify your domain for better deliverability

### Option 2: Use Console Backend (Development Only)
For testing purposes, emails will be logged to console instead of sent.

#### Setup:
1. **Set Environment Variable**
   - In Render dashboard, add: `EMAIL_BACKEND=console`

2. **Check Logs**
   - Emails will appear in Render service logs
   - Useful for testing email content

### Option 3: Use Alternative Email Services
Other services that work with Render:
- **Mailgun**: Similar to SendGrid
- **Amazon SES**: AWS email service
- **Postmark**: Transactional email service

## Testing Email Configuration

### Run Diagnostic Commands:
```bash
# Test SMTP configuration
python manage.py debug_render_smtp

# Test email sending
python manage.py test_render_email --email your-email@example.com
```

### Check Email Status:
```python
from core.render_email_fallback import get_render_email_status
print(get_render_email_status())
```

## Current Implementation

The system now includes:
- ✅ **Automatic detection** of Render hosting
- ✅ **SendGrid integration** as primary email method
- ✅ **SMTP fallback** for local development
- ✅ **Email logging** when no email service is configured
- ✅ **Error handling** to prevent application crashes

## Troubleshooting

### Common Issues:

1. **"Network unreachable" error**
   - This is expected on Render
   - Solution: Use SendGrid or console backend

2. **Emails not being sent**
   - Check Render logs for email content
   - Verify SendGrid API key is correct
   - Check if domain is verified in SendGrid

3. **SendGrid API errors**
   - Verify API key has correct permissions
   - Check if you've exceeded free tier limits
   - Ensure sender email is verified

### Debug Steps:
1. Check environment variables in Render dashboard
2. Run diagnostic commands
3. Check Render service logs
4. Verify SendGrid account status

## Email Flow on Render

1. **Donation emails** → `send_email_with_smtp_config()` → `send_email_with_fallback()`
2. **If SendGrid configured** → Send via SendGrid API
3. **If SendGrid fails** → Try SMTP (will likely fail)
4. **If SMTP fails** → Log email content to console
5. **Return success** to prevent application errors

This ensures your application continues to work even when email sending fails.
