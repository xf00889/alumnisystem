# Email Verification

## Overview

Email Verification is a security feature that confirms you own the email address associated with your account. After registering, you must verify your email before you can log in and access the NORSU Alumni System. This process helps prevent unauthorized account creation and ensures account security.

## Who Can Use This Feature

- **New users** who have just registered
- **Users with unverified email addresses**
- **Users who need to resend verification codes**

## Prerequisites

- Completed registration form
- Valid email address
- Access to your email account
- Internet connection

## How to Access

### After Registration
1. Complete the registration process
2. You're automatically redirected to the email verification page
3. Or visit: `/accounts/verify-email/`

### If You Need to Verify Later
1. Try to log in
2. System will redirect you to verification page if email is not verified
3. Or go directly to `/accounts/verify-email/`

## Key Features

- **6-Digit Verification Code**: Secure code sent to your email
- **Time-Limited Codes**: Codes expire after 15 minutes for security
- **Resend Option**: Request new code if needed
- **Rate Limiting**: Protection against abuse (3 attempts per 15 minutes)
- **Auto-Login**: Automatically logged in after successful verification
- **Email Confirmation**: Receive confirmation when verified

## Step-by-Step Guide

### Task 1: Initial Email Verification (After Registration)

1. **Complete registration**
   - Fill out and submit the registration form
   - **Expected Result**: Registration is successful

2. **Receive redirect to verification page**
   - You're automatically sent to the email verification page
   - You see a message: "Please check your email for verification code"
   - **Expected Result**: Verification page is displayed

3. **Check your email inbox**
   - Look for email from NORSU Alumni System
   - Subject: "Verify your email address" or "Email Verification Code"
   - **Expected Result**: Email arrives within 1-2 minutes

4. **If you don't see the email**
   - Check your spam/junk folder
   - Wait a few minutes and refresh your inbox
   - Verify you entered the correct email during registration
   - **Expected Result**: Email is found

5. **Open the verification email**
   - **Email contains**:
     - Welcome message
     - 6-digit verification code (e.g., 123456)
     - Code expiration time (15 minutes)
     - Instructions
     - Security notice
   - **Expected Result**: Email opens successfully

6. **Copy the verification code**
   - The code is 6 digits
   - Code is case-sensitive (though usually all numbers)
   - **Expected Result**: Code is copied or memorized

7. **Return to the verification page**
   - Go back to your browser with the verification page
   - Or navigate to `/accounts/verify-email/`
   - **Expected Result**: Verification form is displayed

8. **Enter your email address**
   - Type the email you used during registration
   - Must match exactly
   - **Expected Result**: Email field is filled

9. **Enter the verification code**
   - Type or paste the 6-digit code from email
   - Enter all 6 digits
   - **Expected Result**: Code is entered

10. **Submit the verification**
    - Click "Verify Email" or "Submit" button
    - **Expected Result**: Code is verified

11. **Receive verification confirmation**
    - You see: "Email verified successfully!"
    - You're automatically logged in
    - **Expected Result**: Success message is displayed

12. **Complete post-registration profile**
    - You're redirected to complete your profile
    - Fill in required information
    - **Expected Result**: Profile completion form appears

13. **Access your dashboard**
    - After completing profile, you're taken to your dashboard
    - Your account is now fully active
    - **Expected Result**: Dashboard is displayed

### Task 2: Resending Verification Code

If your code expires or you don't receive it:

1. **On the verification page**
   - Look for "Resend Code" or "Didn't receive code?" link
   - Usually below the verification form
   - **Expected Result**: Resend option is visible

2. **Check countdown timer (if present)**
   - You may need to wait 60 seconds between resend attempts
   - Timer shows remaining time
   - **Expected Result**: Timer counts down to zero

3. **Click "Resend Verification Code" button**
   - **Expected Result**: Request is submitted

4. **Receive confirmation message**
   - You see: "New verification code sent to your email"
   - **Expected Result**: Confirmation is displayed

5. **Check your email for new code**
   - A new 6-digit code is sent
   - Previous code is invalidated
   - **Expected Result**: New email arrives within 1-2 minutes

6. **Open the new verification email**
   - Subject: "New Verification Code" or similar
   - Contains fresh 6-digit code
   - **Expected Result**: Email opens successfully

7. **Enter the new code**
   - Use the most recent code received
   - Old codes will not work
   - **Expected Result**: New code is entered

8. **Submit verification**
   - Click "Verify Email" button
   - **Expected Result**: Verification succeeds

### Task 3: Verifying Email After Failed Login Attempt

If you try to log in before verifying:

1. **Attempt to log in**
   - Enter your email and password on login page
   - Click "Sign In"
   - **Expected Result**: Login is attempted

2. **Receive verification reminder**
   - You see: "Please verify your email address first"
   - You're redirected to verification page
   - **Expected Result**: Verification page is displayed

3. **Follow verification process**
   - Check email for verification code
   - Enter code on verification page
   - Submit verification
   - **Expected Result**: Email is verified

4. **Automatic login**
   - After verification, you're automatically logged in
   - No need to go back to login page
   - **Expected Result**: You're logged into your account

### Task 4: Checking Verification Status

To check if your email is verified:

1. **Try to log in**
   - If email is not verified, you'll be redirected to verification page
   - If email is verified, you'll log in successfully
   - **Expected Result**: Status is clear

2. **Check email for confirmation**
   - Look for "Email Verified Successfully" email
   - This confirms verification was completed
   - **Expected Result**: Confirmation email is found

3. **Contact support if unsure**
   - Administrators can check verification status
   - Provide your registered email address
   - **Expected Result**: Status is confirmed

## Tips and Best Practices

### Email Management
- **Use Valid Email**: Ensure you have access to the email you register with
- **Check Spam Folder**: Verification emails may be filtered as spam
- **Whitelist Sender**: Add NORSU Alumni System to your contacts
- **Keep Email Active**: Maintain access to your registered email
- **Update Email**: Contact support if you need to change email address

### Verification Process
- **Verify Promptly**: Complete verification within 15 minutes of receiving code
- **Use Latest Code**: Always use the most recent code if you resend
- **Don't Share Codes**: Verification codes are for your use only
- **Save Confirmation**: Keep the verification confirmation email
- **Complete Profile**: Finish post-registration profile setup after verification

### Security
- **Verify Official Emails**: Ensure emails are from official NORSU Alumni System
- **Don't Click Suspicious Links**: Only use codes, not links in emails
- **Report Phishing**: Report suspicious emails to administrators
- **Secure Email Account**: Use strong password for your email account

## Common Use Cases

### Use Case 1: Standard Registration Flow
- Register for account
- Receive verification email immediately
- Enter code within 15 minutes
- Automatically logged in after verification
- Complete profile setup

### Use Case 2: Delayed Verification
- Register but don't verify immediately
- Try to log in later
- Redirected to verification page
- Request new code (old one expired)
- Complete verification and log in

### Use Case 3: Email Not Received
- Register and wait for email
- Email doesn't arrive after 5 minutes
- Check spam folder
- Use "Resend Code" option
- Receive new code and verify

### Use Case 4: Multiple Resend Attempts
- First code expires
- Request new code
- Still having issues
- Wait for rate limit to reset (15 minutes)
- Request another code and verify

## Troubleshooting

### Issue: Verification email not received
**Symptoms**: No email after registration or resend

**Solution**:
- Check spam/junk folder thoroughly
- Wait 5-10 minutes (email may be delayed)
- Verify you entered correct email during registration
- Check if email provider is blocking emails
- Try resending the code
- Add noreply@norsu-alumni.com to contacts
- Check email storage (full inbox may reject emails)
- Try different email provider if issue persists
- Contact support with your registered email

### Issue: Verification code expired
**Symptoms**: "Code expired" or "Invalid code" error

**Solution**:
- Codes expire after 15 minutes for security
- Click "Resend Code" to get a new code
- Enter the new code promptly
- Complete verification within 15 minutes
- Don't use old codes from previous emails

### Issue: Verification code not working
**Symptoms**: "Invalid code" error when entering correct code

**Solution**:
- Ensure you're using the most recent code
- Check for typos (codes are 6 digits)
- Verify you're entering all 6 digits
- Make sure code hasn't expired
- Try copying and pasting code
- Request a new code if needed
- Ensure email address matches registration

### Issue: Too many resend attempts
**Symptoms**: "Too many attempts" error message

**Solution**:
- Rate limiting prevents abuse (3 attempts per 15 minutes)
- Wait 15-30 minutes before trying again
- Ensure you're using correct email address
- Check spam folder for existing codes
- Contact support if you need immediate access

### Issue: Wrong email address used during registration
**Symptoms**: Cannot access email to get verification code

**Solution**:
- Unfortunately, you cannot change email after registration
- You'll need to register again with correct email
- Contact support to delete the incorrect account
- Use correct email for new registration
- Verify email promptly after new registration

### Issue: Already verified but system asks again
**Symptoms**: System says email needs verification but you already verified

**Solution**:
- Try logging out and back in
- Clear browser cache and cookies
- Try different browser
- Check if you're using correct email address
- Contact support to check verification status
- May need to verify again if there was a system issue

### Issue: Automatic login not working after verification
**Symptoms**: Verified email but not automatically logged in

**Solution**:
- This is rare but can happen
- Simply go to login page
- Enter your email and password
- You should be able to log in now
- Contact support if login still fails

### Issue: Verification page not loading
**Symptoms**: Cannot access verification page

**Solution**:
- Check internet connection
- Try refreshing the page
- Clear browser cache
- Try different browser
- Ensure JavaScript is enabled
- Try accessing directly: `/accounts/verify-email/`
- Contact support if page consistently fails to load

### Issue: Email address field pre-filled with wrong email
**Symptoms**: Verification form shows different email than expected

**Solution**:
- Clear the field and enter correct email
- Ensure it matches your registration email exactly
- Check for typos
- If you registered with wrong email, need to register again
- Contact support for assistance

## Security Features

### Code Generation
- **Random 6-Digit Codes**: Cryptographically secure random generation
- **Time-Limited**: Codes expire after 15 minutes
- **One-Time Use**: Each code can only be used once
- **Unique Per User**: Each user gets unique code

### Rate Limiting
- **3 Resend Attempts**: Maximum 3 resends per 15 minutes
- **Prevents Abuse**: Stops automated attacks
- **Fair Usage**: Allows legitimate users to resend if needed
- **Automatic Reset**: Limit resets after 15 minutes

### Email Security
- **Sender Verification**: Emails sent from verified domain
- **Secure Transmission**: Emails sent over secure connection
- **No Sensitive Data**: Only verification code in email
- **Clear Instructions**: Helps users identify legitimate emails

### Audit Logging
- **All Attempts Logged**: Verification attempts are recorded
- **IP Address Tracked**: Logs where verification originated
- **Timestamp Recorded**: When verification occurred
- **Security Monitoring**: Helps detect suspicious activity

## What Happens After Verification

Once you verify your email:

1. **Account Activated**: Your account becomes active
2. **Auto-Login**: You're automatically logged in
3. **Profile Setup**: Redirected to complete profile
4. **Confirmation Email**: Receive verification confirmation
5. **Full Access**: Can access all authenticated features
6. **Security Log**: Verification is recorded for audit

## What Happens If You Don't Verify

If you don't verify your email:

1. **Cannot Log In**: Login attempts are blocked
2. **Account Inactive**: Account remains inactive
3. **Limited Access**: Cannot use authenticated features
4. **Codes Expire**: Old codes become invalid after 15 minutes
5. **Can Resend**: Can request new codes anytime
6. **Account Cleanup**: Unverified accounts may be deleted after extended period

## Related Features

- [Registration Process](../../public-features/registration.md) - Create a new account
- [Login and Logout](login-logout.md) - Access your account
- [Password Management](password-management.md) - Manage your password
- [Profile Management](../profile-management/README.md) - Update your profile

## Additional Notes

### Verification Code Format
- **6 digits**: Always numeric (0-9)
- **No spaces**: Enter as continuous string
- **Case-insensitive**: Though usually all numbers
- **Example**: 123456, 789012, 456789

### Email Delivery Time
- **Usually instant**: Most emails arrive within 1-2 minutes
- **Maximum wait**: Up to 10 minutes in rare cases
- **Check spam**: May be filtered by email provider
- **Provider delays**: Some providers may delay delivery

### Code Expiration
- **15 minutes**: Standard expiration time
- **Security measure**: Prevents old codes from being used
- **Countdown**: Some interfaces show time remaining
- **Automatic invalidation**: Old codes stop working after expiration

### Browser Compatibility
- Works with all modern browsers
- JavaScript must be enabled
- Cookies must be enabled
- Recommended to use latest browser version

### Mobile Access
- Fully responsive on mobile devices
- Can copy/paste codes on mobile
- Touch-friendly interface
- Same process as desktop

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the [Troubleshooting Guide](../../resources/troubleshooting.md).

*Last Updated: November 19, 2025*
