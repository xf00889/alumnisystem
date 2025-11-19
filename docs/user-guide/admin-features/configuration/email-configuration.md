# Email Configuration

## Overview

The Email Configuration feature allows administrators to set up and manage email delivery settings for the NORSU Alumni System. The system supports multiple email providers including SMTP (Gmail, Outlook, Yahoo, custom servers), Brevo, and SendGrid. You can configure multiple email providers and switch between them as needed.

## Who Can Use This Feature

- **User Role**: Admin users and superusers only
- **Permissions Required**: Staff or superuser status
- **Prerequisites**: 
  - Admin access to the system
  - Email provider credentials (SMTP username/password or API keys)
  - For Gmail/Yahoo: App Password (requires 2FA enabled)

## How to Access

1. Log in to the system with admin credentials
2. Navigate to the admin dashboard
3. Click on "Email Configuration" or access via URL: `/admin/core/email-configuration/`
4. You will see a list of all configured email providers

## Key Features

- Configure multiple email providers (SMTP, Brevo, SendGrid)
- Quick setup wizard for popular email providers (Gmail, Outlook, Yahoo)
- Test email configurations before activation
- Switch between different email providers
- View configuration status and last test results
- Secure storage of email credentials
- Support for TLS/SSL encryption

## Step-by-Step Guide

### Task 1: Quick Setup with Gmail

The quickest way to set up email is using the Quick Setup wizard with a popular provider like Gmail.

1. **Access Quick Setup**
   - From the Email Configuration list page, click the "Quick Setup" button
   - **Expected Result**: You'll see the Quick Setup wizard with provider options

2. **Select Gmail as Provider**
   - Choose "Gmail" from the provider options
   - **Expected Result**: The form will show Gmail-specific instructions

3. **Enter Gmail Credentials**
   - **Email Address**: Enter your Gmail address (e.g., `your-email@gmail.com`)
   - **App Password**: Enter your Gmail App Password (NOT your regular password)
   - **From Name**: Enter the sender name (e.g., "NORSU Alumni System")
   - **Note**: You must have 2-Factor Authentication enabled and create an App Password in your Google Account settings
   - **Expected Result**: Form fields are filled with your information

4. **Create and Test Configuration**
   - Click "Create and Test" button
   - The system will create the configuration and automatically test it
   - **Expected Result**: Success message appears if the configuration works, or error message with details if it fails

5. **Verify Active Status**
   - Return to the Email Configuration list
   - Your Gmail configuration should show as "Active"
   - **Expected Result**: Green "Active" badge next to your configuration

### Task 2: Quick Setup with Outlook/Hotmail

1. **Access Quick Setup**
   - From the Email Configuration list page, click "Quick Setup"

2. **Select Outlook as Provider**
   - Choose "Outlook/Hotmail" from the provider options

3. **Enter Outlook Credentials**
   - **Email Address**: Enter your Outlook/Hotmail address
   - **Password**: Enter your regular Outlook password
   - **From Name**: Enter the sender name
   - **Expected Result**: Form is ready for submission

4. **Create and Test**
   - Click "Create and Test" button
   - **Expected Result**: Configuration is created and tested automatically

### Task 3: Quick Setup with Brevo

1. **Access Quick Setup**
   - From the Email Configuration list page, click "Quick Setup"

2. **Select Brevo as Provider**
   - Choose "Brevo" from the provider options

3. **Enter Brevo Credentials**
   - **API Key**: Enter your Brevo API key (from Brevo dashboard)
   - **From Email**: Enter the verified sender email in Brevo
   - **From Name**: Enter the sender name
   - **Expected Result**: Form is ready for submission

4. **Create and Test**
   - Click "Create and Test" button
   - **Expected Result**: Brevo configuration is created and tested

### Task 4: Manual SMTP Configuration

For custom SMTP servers or advanced configurations:

1. **Access Configuration Form**
   - From the Email Configuration list, click "Add SMTP Configuration"
   - **Expected Result**: Empty configuration form appears

2. **Enter Basic Information**
   - **Name**: Give your configuration a descriptive name (e.g., "Company SMTP Server")
   - **Host**: Enter the SMTP server hostname (e.g., `smtp.example.com`)
   - **Port**: Enter the SMTP port (usually 587 for TLS, 465 for SSL, 25 for unencrypted)
   - **Expected Result**: Basic fields are filled

3. **Configure Security Settings**
   - **Use TLS**: Check this for STARTTLS encryption (port 587)
   - **Use SSL**: Check this for SSL/TLS encryption (port 465)
   - **Note**: Usually only one should be checked, not both
   - **Expected Result**: Security options are selected

4. **Enter Authentication Details**
   - **Username**: Enter SMTP username (often the email address)
   - **Password**: Enter SMTP password
   - **From Email**: Enter the sender email address
   - **From Name**: Enter the sender name (optional)
   - **Expected Result**: All authentication fields are filled

5. **Set Active Status**
   - **Is Active**: Check this box to make this the active configuration
   - **Note**: Only one configuration can be active at a time
   - **Expected Result**: Configuration is marked for activation

6. **Save Configuration**
   - Click "Save" button
   - **Expected Result**: Configuration is saved and you're redirected to the list

### Task 5: Testing Email Configuration

1. **Locate Configuration to Test**
   - From the Email Configuration list, find the configuration you want to test
   - **Expected Result**: Configuration is visible in the list

2. **Initiate Test**
   - Click the "Test" button next to the configuration
   - **Expected Result**: Test dialog appears

3. **Enter Test Email Address**
   - Enter the email address where you want to receive the test email
   - Default is the configuration's username/email
   - **Expected Result**: Email address is entered

4. **Send Test Email**
   - Click "Send Test Email" button
   - The system will attempt to send a test email
   - **Expected Result**: Success or error message appears

5. **Verify Test Results**
   - Check the recipient inbox for the test email
   - The email subject will be "Test Email from NORSU Alumni System"
   - **Expected Result**: Test email is received if configuration is correct

### Task 6: Switching Between Email Providers

1. **View Available Configurations**
   - Go to the Email Configuration list
   - Review all configured providers
   - **Expected Result**: All configurations are listed with their status

2. **Activate Different Configuration**
   - Find the configuration you want to activate
   - Click the "Activate" button next to it
   - **Expected Result**: Confirmation dialog appears

3. **Confirm Activation**
   - Confirm that you want to switch to this configuration
   - **Expected Result**: The selected configuration becomes active, others are deactivated

4. **Verify Active Status**
   - The newly activated configuration shows a green "Active" badge
   - Previously active configuration no longer shows as active
   - **Expected Result**: Only one configuration is active

### Task 7: Editing Email Configuration

1. **Select Configuration to Edit**
   - From the Email Configuration list, find the configuration
   - Click the "Edit" button or configuration name
   - **Expected Result**: Edit form appears with current values

2. **Modify Settings**
   - Update any fields as needed (host, port, credentials, etc.)
   - **Expected Result**: Changes are reflected in the form

3. **Save Changes**
   - Click "Save" button
   - **Expected Result**: Configuration is updated and you're redirected to the list

4. **Test After Changes**
   - It's recommended to test the configuration after editing
   - Click "Test" to verify the changes work correctly
   - **Expected Result**: Test confirms the updated configuration works

### Task 8: Deleting Email Configuration

1. **Select Configuration to Delete**
   - From the Email Configuration list, find the configuration
   - **Note**: You cannot delete the currently active configuration
   - **Expected Result**: Delete button is available for inactive configurations

2. **Initiate Deletion**
   - Click the "Delete" button
   - **Expected Result**: Confirmation dialog appears

3. **Confirm Deletion**
   - Confirm that you want to delete the configuration
   - **Warning**: This action cannot be undone
   - **Expected Result**: Configuration is permanently deleted

## Tips and Best Practices

- **Use App Passwords**: For Gmail and Yahoo, always use App Passwords instead of your regular password. This requires enabling 2-Factor Authentication first.
- **Test Before Activating**: Always test a new configuration before activating it to ensure emails will be delivered.
- **Keep Backup Configuration**: Maintain at least two working configurations in case one fails.
- **Monitor Test Results**: Regularly test your active configuration to ensure it's still working.
- **Secure Credentials**: Never share your SMTP passwords or API keys. They are stored securely in the database.
- **Use TLS Encryption**: Always use TLS or SSL encryption for security (ports 587 or 465).
- **Verify Sender Email**: For Brevo and SendGrid, ensure your sender email is verified in their dashboard.

## Common Use Cases

### Use Case 1: Setting Up Gmail for Development
During development, use Gmail with an App Password for quick and reliable email delivery. This is ideal for testing email features without setting up a dedicated email server.

### Use Case 2: Using Brevo for Production
For production environments, use Brevo (formerly Sendinblue) for better deliverability, analytics, and higher sending limits. Brevo offers a free tier suitable for most alumni systems.

### Use Case 3: Switching Providers During Outage
If your primary email provider experiences issues, quickly switch to a backup configuration to maintain email functionality without system downtime.

## Troubleshooting

### Issue: Gmail Authentication Failed
**Symptoms**: Test email fails with "Authentication failed" error
**Solution**: 
- Ensure 2-Factor Authentication is enabled on your Google Account
- Create an App Password in Google Account settings (Security > 2-Step Verification > App passwords)
- Use the App Password (16 characters without spaces) instead of your regular password
- Ensure "Less secure app access" is NOT needed with App Passwords

### Issue: Connection Timeout
**Symptoms**: Test email fails with "Connection timeout" or "Cannot connect to server"
**Solution**:
- Verify the SMTP host and port are correct
- Check if your firewall or network blocks the SMTP port
- Try alternative ports (587 for TLS, 465 for SSL)
- Ensure your server has internet connectivity

### Issue: TLS/SSL Errors
**Symptoms**: Test email fails with SSL or TLS certificate errors
**Solution**:
- Ensure only one of "Use TLS" or "Use SSL" is checked, not both
- Use port 587 with TLS or port 465 with SSL
- Verify the SMTP server supports the encryption method you selected

### Issue: Brevo API Key Invalid
**Symptoms**: Brevo test fails with "Invalid API key" error
**Solution**:
- Verify you copied the complete API key from Brevo dashboard
- Ensure the API key has SMTP permissions enabled
- Check that your Brevo account is active and verified
- Generate a new API key if the old one was revoked

### Issue: Emails Not Being Received
**Symptoms**: Test shows success but email never arrives
**Solution**:
- Check the recipient's spam/junk folder
- Verify the sender email is not blacklisted
- For Brevo/SendGrid, ensure the sender email is verified
- Check email provider's sending logs for delivery status

### Issue: Cannot Activate Configuration
**Symptoms**: Activation button doesn't work or shows error
**Solution**:
- Test the configuration first to ensure it works
- Only one configuration can be active at a time
- Refresh the page and try again
- Check browser console for JavaScript errors

## Related Features

- [System Configuration](./README.md) - Overview of all system configuration options
- [reCAPTCHA Configuration](./recaptcha-configuration.md) - Configure spam protection
- [Announcement Management](../announcements/creating-announcements.md) - Announcements can trigger email notifications
- [Event Management](../events/creating-events.md) - Events can send email invitations

## Additional Notes

### Email Provider Comparison

**SMTP (Gmail, Outlook, Yahoo)**
- Pros: Easy to set up, no additional accounts needed, free
- Cons: Lower sending limits, may be blocked by some networks, less reliable for bulk emails
- Best for: Development, testing, small deployments

**Brevo (formerly Sendinblue)**
- Pros: Free tier (300 emails/day), good deliverability, analytics, templates
- Cons: Requires separate account, sender email verification needed
- Best for: Production environments, regular email communications

**SendGrid**
- Pros: High deliverability, detailed analytics, scalable
- Cons: Requires separate account, free tier limited (100 emails/day)
- Best for: Large-scale deployments, high-volume email sending

### Security Considerations

- All passwords and API keys are encrypted in the database
- Use environment variables for sensitive credentials in production
- Regularly rotate API keys and passwords
- Monitor email sending logs for suspicious activity
- Disable unused configurations to reduce security risks

### Gmail App Password Setup

1. Go to your Google Account (myaccount.google.com)
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled
4. Under "2-Step Verification", find "App passwords"
5. Select "Mail" and "Other (Custom name)"
6. Enter "NORSU Alumni System" as the name
7. Click "Generate"
8. Copy the 16-character password (without spaces)
9. Use this password in the Email Configuration

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the system documentation.

*Last Updated: November 19, 2025*
