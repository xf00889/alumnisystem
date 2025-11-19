# Recaptcha Configuration

## Overview

The reCAPTCHA Configuration feature allows administrators to set up and manage Google reCAPTCHA v3 protection for the NORSU Alumni System. reCAPTCHA helps protect your system from spam and abuse by analyzing user interactions and assigning risk scores. The system supports multiple reCAPTCHA configurations and provides analytics to monitor protection effectiveness.

## Who Can Use This Feature

- **User Role**: Admin users and superusers only
- **Permissions Required**: Staff or superuser status
- **Prerequisites**: 
  - Admin access to the system
  - Google reCAPTCHA v3 site key and secret key
  - Google account to access reCAPTCHA Admin Console

## How to Access

1. Log in to the system with admin credentials
2. Navigate to the admin dashboard
3. Click on "reCAPTCHA Configuration" or access via URL: `/admin/core/recaptcha-configuration/`
4. You will see a list of all configured reCAPTCHA settings

## Key Features

- Configure Google reCAPTCHA v3 protection
- Set custom score thresholds for spam detection
- Enable/disable reCAPTCHA without deleting configuration
- Test reCAPTCHA configuration before activation
- View real-time analytics and metrics
- Monitor success rates and spam reduction
- Track reCAPTCHA performance by form type
- Switch between multiple configurations

## Step-by-Step Guide

### Task 1: Getting reCAPTCHA Keys from Google

Before configuring reCAPTCHA in the system, you need to obtain keys from Google.

1. **Access Google reCAPTCHA Admin Console**
   - Go to https://www.google.com/recaptcha/admin
   - Sign in with your Google account
   - **Expected Result**: You see the reCAPTCHA Admin Console

2. **Register a New Site**
   - Click the "+" button or "Register a new site"
   - **Expected Result**: Registration form appears

3. **Fill in Site Details**
   - **Label**: Enter a descriptive name (e.g., "NORSU Alumni System")
   - **reCAPTCHA type**: Select "reCAPTCHA v3"
   - **Domains**: Enter your domain(s) (e.g., `alumni.norsu.edu.ph`)
     - For development, add `localhost` and `127.0.0.1`
   - **Accept reCAPTCHA Terms of Service**: Check the box
   - **Expected Result**: Form is filled with your information

4. **Submit Registration**
   - Click "Submit" button
   - **Expected Result**: You receive your site key and secret key

5. **Copy Your Keys**
   - **Site Key**: Copy this key (starts with "6L...")
   - **Secret Key**: Copy this key (starts with "6L...")
   - **Note**: Keep the secret key confidential
   - **Expected Result**: Both keys are copied for use in the system

### Task 2: Creating reCAPTCHA Configuration

1. **Access Configuration Form**
   - From the reCAPTCHA Configuration list, click "Add reCAPTCHA Configuration"
   - **Expected Result**: Empty configuration form appears

2. **Enter Configuration Name**
   - **Name**: Give your configuration a descriptive name (e.g., "Production reCAPTCHA")
   - **Expected Result**: Name field is filled

3. **Enter reCAPTCHA Keys**
   - **Site Key**: Paste the site key from Google reCAPTCHA Admin Console
   - **Secret Key**: Paste the secret key from Google reCAPTCHA Admin Console
   - **Expected Result**: Both keys are entered

4. **Set Score Threshold**
   - **Threshold**: Enter a value between 0.0 and 1.0 (default: 0.5)
     - 0.0 = Most lenient (allows more users, may allow some bots)
     - 1.0 = Most strict (blocks more bots, may block some legitimate users)
     - 0.5 = Balanced (recommended starting point)
   - **Expected Result**: Threshold is set

5. **Configure Status**
   - **Is Active**: Check to make this the active configuration
   - **Enabled**: Check to enable reCAPTCHA protection
   - **Note**: Only one configuration can be active at a time
   - **Expected Result**: Status options are selected

6. **Save Configuration**
   - Click "Save" button
   - **Expected Result**: Configuration is saved and you're redirected to the list

### Task 3: Testing reCAPTCHA Configuration

1. **Locate Configuration to Test**
   - From the reCAPTCHA Configuration list, find your configuration
   - **Expected Result**: Configuration is visible in the list

2. **Initiate Test**
   - Click the "Test" button next to the configuration
   - **Expected Result**: Test process begins

3. **Review Test Results**
   - The system will verify the keys with Google's API
   - **Success**: "Configuration test successful" message appears
   - **Failure**: Error message with details appears
   - **Expected Result**: You know if the configuration is working

4. **Troubleshoot if Needed**
   - If test fails, verify your keys are correct
   - Check that your domain is registered in Google reCAPTCHA Admin Console
   - Ensure your server can connect to Google's API
   - **Expected Result**: Issues are identified and resolved

### Task 4: Adjusting Score Threshold

The score threshold determines how strict reCAPTCHA is in detecting bots.

1. **Access Configuration**
   - Click "Edit" on your reCAPTCHA configuration
   - **Expected Result**: Edit form appears

2. **Understand Score Ranges**
   - **0.9 - 1.0**: Very likely a legitimate user
   - **0.7 - 0.9**: Probably a legitimate user
   - **0.5 - 0.7**: Neutral (could be either)
   - **0.3 - 0.5**: Possibly a bot
   - **0.0 - 0.3**: Very likely a bot

3. **Adjust Threshold Based on Needs**
   - **For high security** (e.g., admin login): Set to 0.6 or higher
   - **For user convenience** (e.g., public forms): Set to 0.4 or lower
   - **For balanced protection**: Keep at 0.5
   - **Expected Result**: Threshold is adjusted

4. **Save and Monitor**
   - Save the changes
   - Monitor the analytics to see how the new threshold affects users
   - **Expected Result**: Threshold is updated and being applied

### Task 5: Enabling/Disabling reCAPTCHA

You can temporarily disable reCAPTCHA without deleting the configuration.

1. **Access Configuration List**
   - Go to the reCAPTCHA Configuration list
   - **Expected Result**: All configurations are visible

2. **Toggle Enabled Status**
   - Find the configuration you want to enable/disable
   - Click the "Toggle Enabled" button
   - **Expected Result**: Confirmation dialog appears

3. **Confirm Action**
   - Confirm that you want to change the enabled status
   - **Expected Result**: Status is toggled

4. **Verify Status**
   - **Enabled**: Green "Enabled" badge appears, reCAPTCHA is active on forms
   - **Disabled**: Gray "Disabled" badge appears, reCAPTCHA is not active
   - **Expected Result**: Status reflects your choice

### Task 6: Viewing reCAPTCHA Analytics

1. **Access Analytics Dashboard**
   - From the admin menu, click "reCAPTCHA Analytics"
   - Or navigate to `/admin/core/recaptcha-analytics/`
   - **Expected Result**: Analytics dashboard appears

2. **Review Overall Metrics**
   - **Total Verifications**: Total number of reCAPTCHA checks performed
   - **Success Rate**: Percentage of users who passed reCAPTCHA
   - **Failure Rate**: Percentage of users who failed reCAPTCHA
   - **Error Rate**: Percentage of verification errors
   - **Expected Result**: You see overall statistics

3. **Analyze Spam Reduction**
   - **Spam Blocked**: Estimated number of spam attempts blocked
   - **Total Attempts**: Total form submission attempts
   - **Reduction Percentage**: Percentage of spam blocked
   - **Expected Result**: You understand how much spam is being prevented

4. **Review Form-Specific Metrics**
   - See breakdown by form type (login, signup, contact, etc.)
   - Identify which forms have the most bot activity
   - **Expected Result**: You know which forms need attention

5. **View Hourly Trends**
   - See reCAPTCHA activity over the last 24 hours
   - Identify peak times for bot activity
   - **Expected Result**: You understand usage patterns

6. **Monitor Success Rates**
   - Check if legitimate users are being blocked
   - If success rate is too low, consider lowering the threshold
   - If spam is getting through, consider raising the threshold
   - **Expected Result**: You can make informed threshold adjustments

### Task 7: Switching Between Configurations

1. **View Available Configurations**
   - Go to the reCAPTCHA Configuration list
   - Review all configured settings
   - **Expected Result**: All configurations are listed

2. **Activate Different Configuration**
   - Find the configuration you want to activate
   - Click the "Activate" button
   - **Expected Result**: Confirmation dialog appears

3. **Confirm Activation**
   - Confirm that you want to switch configurations
   - **Expected Result**: Selected configuration becomes active

4. **Verify Active Status**
   - The newly activated configuration shows a green "Active" badge
   - Previously active configuration no longer shows as active
   - **Expected Result**: Only one configuration is active

### Task 8: Deleting reCAPTCHA Configuration

1. **Select Configuration to Delete**
   - From the reCAPTCHA Configuration list, find the configuration
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

- **Start with Default Threshold**: Begin with 0.5 and adjust based on analytics data
- **Monitor Analytics Regularly**: Check analytics weekly to ensure reCAPTCHA is working effectively
- **Don't Set Threshold Too High**: A threshold above 0.7 may block legitimate users
- **Test After Changes**: Always test configuration after making changes
- **Keep Backup Configuration**: Maintain a second configuration for quick switching if needed
- **Secure Secret Key**: Never share or expose your secret key publicly
- **Register All Domains**: Include all domains where your system is accessible (including localhost for development)
- **Review Spam Patterns**: Use analytics to identify peak spam times and adjust accordingly
- **Balance Security and UX**: Find the right threshold that blocks spam without frustrating users

## Common Use Cases

### Use Case 1: Setting Up for Production
Configure reCAPTCHA with a balanced threshold (0.5) for production deployment. Monitor analytics for the first week and adjust threshold based on false positive/negative rates.

### Use Case 2: High-Security Forms
For sensitive forms like admin login or password reset, create a separate configuration with a higher threshold (0.6-0.7) to provide extra protection.

### Use Case 3: Temporary Disable During Testing
Disable reCAPTCHA temporarily during user acceptance testing or when troubleshooting form issues, then re-enable when testing is complete.

### Use Case 4: Responding to Spam Attack
If analytics show a sudden increase in bot activity, quickly raise the threshold or switch to a stricter configuration to block the attack.

## Troubleshooting

### Issue: Test Configuration Fails
**Symptoms**: Test shows "Configuration test failed" error
**Solution**:
- Verify site key and secret key are correct and complete
- Check that keys are from reCAPTCHA v3 (not v2)
- Ensure your domain is registered in Google reCAPTCHA Admin Console
- Verify your server has internet connectivity to reach Google's API
- Check for typos or extra spaces in the keys

### Issue: Legitimate Users Being Blocked
**Symptoms**: Users report they cannot submit forms, success rate is below 80%
**Solution**:
- Lower the score threshold (try 0.4 or 0.3)
- Check analytics to see which forms have the highest failure rate
- Verify reCAPTCHA is not conflicting with browser extensions
- Ensure users have JavaScript enabled
- Consider if your user base has unique characteristics (e.g., VPN usage)

### Issue: Spam Still Getting Through
**Symptoms**: Spam submissions despite reCAPTCHA being enabled
**Solution**:
- Raise the score threshold (try 0.6 or 0.7)
- Verify reCAPTCHA is actually enabled (check "Enabled" status)
- Ensure the active configuration is the one you expect
- Check that forms are properly implementing reCAPTCHA
- Review analytics to confirm reCAPTCHA is running on the affected forms

### Issue: reCAPTCHA Not Appearing on Forms
**Symptoms**: No reCAPTCHA badge visible on forms
**Solution**:
- Verify reCAPTCHA is enabled (not just active)
- Check that at least one configuration exists and is active
- Clear browser cache and reload the page
- Check browser console for JavaScript errors
- Verify site key is correct in the configuration

### Issue: Analytics Showing No Data
**Symptoms**: Analytics dashboard shows all zeros
**Solution**:
- Verify reCAPTCHA is enabled and active
- Ensure users are actually submitting forms
- Check that forms are properly instrumented with reCAPTCHA
- Wait a few minutes for cache to update
- Try submitting a test form yourself

### Issue: High Error Rate in Analytics
**Symptoms**: Error rate above 5% in analytics
**Solution**:
- Check server logs for reCAPTCHA API errors
- Verify server can connect to Google's API (check firewall)
- Ensure secret key is correct
- Check for rate limiting from Google (unlikely but possible)
- Verify system time is synchronized (important for API calls)

### Issue: Cannot Activate Configuration
**Symptoms**: Activation button doesn't work
**Solution**:
- Test the configuration first to ensure it works
- Only one configuration can be active at a time
- Refresh the page and try again
- Check browser console for JavaScript errors
- Verify you have admin permissions

## Related Features

- [Email Configuration](./email-configuration.md) - Configure email delivery settings
- [System Configuration](./README.md) - Overview of all system configuration options
- [User Management](../user-management/viewing-users.md) - Monitor user accounts for suspicious activity
- [Feedback Management](../../user-features/feedback/submitting-feedback.md) - Forms protected by reCAPTCHA

## Additional Notes

### Understanding reCAPTCHA v3

reCAPTCHA v3 is different from v2:
- **No user interaction**: Users don't need to click "I'm not a robot" or solve puzzles
- **Score-based**: Returns a score (0.0-1.0) indicating likelihood of being a bot
- **Invisible**: Runs in the background without interrupting user experience
- **Context-aware**: Analyzes user behavior across your site

### Score Interpretation

Google provides these general guidelines:
- **1.0**: Very likely a good interaction
- **0.9**: Very likely a good interaction
- **0.8**: Likely a good interaction
- **0.7**: Likely a good interaction
- **0.6**: Neutral
- **0.5**: Neutral (default threshold)
- **0.4**: Possibly risky
- **0.3**: Possibly risky
- **0.2**: Likely risky
- **0.1**: Very likely risky
- **0.0**: Very likely a bot

### Privacy Considerations

- reCAPTCHA collects user data to function (IP address, cookies, browser info)
- Ensure your privacy policy mentions reCAPTCHA usage
- Google's privacy policy applies: https://policies.google.com/privacy
- Users in privacy-sensitive regions may need additional disclosures

### Performance Impact

- reCAPTCHA v3 has minimal performance impact
- Loads asynchronously and doesn't block page rendering
- Adds approximately 50-100KB to page size
- API calls are fast (typically <100ms)

### Domain Registration

When registering domains in Google reCAPTCHA Admin Console:
- Use the exact domain without protocol (e.g., `alumni.norsu.edu.ph`, not `https://alumni.norsu.edu.ph`)
- Add `localhost` for local development
- Add `127.0.0.1` for local development
- Wildcards are supported (e.g., `*.norsu.edu.ph`)
- You can add multiple domains to one configuration

### Monitoring Best Practices

- Check analytics at least weekly
- Set up alerts for sudden changes in success rate
- Review form-specific metrics to identify problem areas
- Track trends over time to identify patterns
- Use analytics to justify threshold adjustments

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the [Google reCAPTCHA documentation](https://developers.google.com/recaptcha/docs/v3).

*Last Updated: November 19, 2025*
