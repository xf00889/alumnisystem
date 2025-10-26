# Donation Email System Documentation

## Overview

The donation email system provides automated email notifications for donation-related events in the NORSU Alumni System. The system sends beautifully designed, responsive emails that maintain consistency with the overall system theme.

## Features

### 📧 Email Types

1. **Donation Confirmation Email** - Sent when a donation is created
2. **Status Update Email** - Sent when donation status changes
3. **Receipt Email** - Sent for completed donations

### 🎨 Design Features

- **Consistent Theme**: Uses the system's color scheme (`#2b3c6b`, `#4a5568`)
- **Responsive Design**: Works on desktop and mobile devices
- **Modern Layout**: Clean, professional appearance with gradients and shadows
- **Brand Consistency**: NORSU Alumni System branding throughout

## File Structure

```
donations/
├── email_utils.py                    # Email sending functions
├── signals.py                        # Django signals for automation
├── management/
│   └── commands/
│       └── test_donation_emails.py   # Test command
└── templates/
    └── emails/
        ├── donation_confirmation.html    # Confirmation email template
        ├── donation_status_update.html  # Status update email template
        └── donation_receipt.html         # Receipt email template
```

## Email Templates

### 1. Donation Confirmation Email (`donation_confirmation.html`)

**Triggered**: When a donation is created
**Purpose**: Thank the donor and provide donation details

**Features**:
- Personalized greeting
- Donation amount prominently displayed
- Campaign information
- Next steps outlined
- Status information
- Donor message (if provided)

### 2. Status Update Email (`donation_status_update.html`)

**Triggered**: When donation status changes
**Purpose**: Keep donors informed of their donation status

**Features**:
- Status-specific messaging
- Visual status badges
- Detailed explanation of what the status means
- Campaign information
- Verification details (if applicable)

### 3. Receipt Email (`donation_receipt.html`)

**Triggered**: For completed donations
**Purpose**: Provide official receipt for tax/record purposes

**Features**:
- Official receipt format
- Detailed donation information
- Campaign impact information
- Professional receipt styling
- Tax-deductible information

## Implementation

### Automatic Email Sending

The system uses Django signals to automatically send emails:

```python
# In donations/signals.py
@receiver(post_save, sender=Donation)
def send_donation_emails(sender, instance, created, **kwargs):
    if created:
        send_donation_confirmation_email(instance)
    else:
        if hasattr(instance, '_old_status') and instance._old_status != instance.status:
            send_donation_status_update_email(instance, instance._old_status)
            if instance.status == 'completed' and not instance.receipt_sent:
                send_donation_receipt_email(instance)
```

### Manual Email Sending

Admins can manually send receipt emails through the admin interface:

```python
# In donations/views.py
@require_POST
@login_required
def send_donation_receipt(request, pk):
    # Admin-only function to manually send receipt emails
```

## Configuration

### SMTP Settings

The system uses the existing SMTP configuration from `core.email_utils`:

```python
# Uses existing SMTP configuration
from core.email_utils import send_email_with_smtp_config
```

### Email Templates Context

Each email template receives the following context variables:

```python
context = {
    'donor_name': donor_name,
    'donor_email': donor_email,
    'amount': donation.amount,
    'reference_number': donation.reference_number,
    'campaign_name': donation.campaign.name,
    'campaign_description': donation.campaign.description,
    'donation_date': donation.donation_date,
    'status': donation.status,
    'status_display': donation.get_status_display(),
    'verification_date': donation.verification_date,
    'verified_by': donation.verified_by,
    'verification_notes': donation.verification_notes,
    'is_anonymous': donation.is_anonymous,
    'message': donation.message,
}
```

## Testing

### Management Command

Test the email functionality using the management command:

```bash
# Test confirmation email
python manage.py test_donation_emails --email your-email@example.com --type confirmation

# Test status update email
python manage.py test_donation_emails --email your-email@example.com --type status

# Test receipt email
python manage.py test_donation_emails --email your-email@example.com --type receipt
```

### Test Script

Run the comprehensive test script:

```bash
python test_donation_emails.py
```

## Email Flow

### 1. Donation Creation Flow

```
User creates donation
    ↓
Django signal triggered
    ↓
send_donation_confirmation_email() called
    ↓
Email sent to donor
```

### 2. Status Change Flow

```
Admin changes donation status
    ↓
Django signal triggered
    ↓
send_donation_status_update_email() called
    ↓
Email sent to donor
    ↓
If status = 'completed':
    send_donation_receipt_email() called
    ↓
Receipt email sent to donor
```

## Customization

### Adding New Email Types

1. Create new template in `templates/emails/`
2. Add function in `donations/email_utils.py`
3. Update signals if needed

### Modifying Templates

All templates use consistent styling:
- Header with NORSU branding
- Responsive design
- System color scheme
- Professional layout

### Adding New Context Variables

Update the context dictionary in the email utility functions:

```python
context = {
    # Existing variables...
    'new_variable': new_value,
}
```

## Error Handling

The system includes comprehensive error handling:

- Logs all email sending attempts
- Graceful failure handling
- SMTP configuration validation
- Email address validation

## Security

- Email addresses are validated before sending
- Anonymous donations are handled appropriately
- Admin-only functions are protected
- No sensitive data in email templates

## Performance

- Emails are sent asynchronously where possible
- Template rendering is optimized
- SMTP connections are reused
- Error handling prevents system slowdowns

## Monitoring

All email activities are logged:

```python
logger.info(f"Donation confirmation email sent to {donor_email} for donation {donation.pk}")
logger.error(f"Failed to send donation confirmation email to {donor_email} for donation {donation.pk}")
```

## Troubleshooting

### Common Issues

1. **Emails not sending**
   - Check SMTP configuration
   - Verify email addresses
   - Check Django logs

2. **Template errors**
   - Verify template syntax
   - Check context variables
   - Test with management command

3. **Signal not triggering**
   - Ensure signals are imported
   - Check Django app configuration
   - Verify model changes

### Debug Mode

Enable debug logging:

```python
import logging
logger = logging.getLogger('donations.email_utils')
logger.setLevel(logging.DEBUG)
```

## Future Enhancements

- Email templates in multiple languages
- Advanced email analytics
- Email scheduling
- Custom email templates per campaign
- Email preferences for donors

## Support

For issues or questions about the donation email system:

1. Check the Django logs
2. Run the test commands
3. Verify SMTP configuration
4. Contact the development team

---

**Last Updated**: December 2024
**Version**: 1.0
**Maintainer**: NORSU Alumni System Development Team
