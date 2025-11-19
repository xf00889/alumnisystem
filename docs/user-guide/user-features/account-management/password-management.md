# Password Management

## Overview

Password Management features allow you to maintain the security of your NORSU Alumni System account by changing your password or resetting it if forgotten. The system enforces strong password requirements and includes security features to protect your account.

## Who Can Use This Feature

- **All registered users** who want to change their password
- **Users who have forgotten their password** and need to reset it
- **Users concerned about account security** who want to update credentials

## Prerequisites

### For Password Change
- Active account with current login access
- Knowledge of current password

### For Password Reset
- Registered email address
- Access to your registered email account

## How to Access

### Change Password (When Logged In)
1. Log in to your account
2. Click on your profile icon/name
3. Select "Account Settings" or "Security"
4. Click "Change Password"

### Reset Password (When Logged Out)
1. Go to the login page
2. Click "Forgot Password?" link
3. Follow the password reset process

## Key Features

- **Password Change**: Update your password while logged in
- **Password Reset**: Recover access if you forget your password
- **Email Verification**: Secure verification via email code
- **Strong Password Requirements**: Enforced security standards
- **Password History**: Prevents reuse of recent passwords
- **Rate Limiting**: Protection against brute force attacks

## Password Requirements

Your password must meet the following criteria:

- **Minimum Length**: At least 8 characters
- **Uppercase Letter**: At least one uppercase letter (A-Z)
- **Lowercase Letter**: At least one lowercase letter (a-z)
- **Number**: At least one digit (0-9)
- **Special Character**: At least one special character (!@#$%^&*)
- **Not Common**: Cannot be a commonly used password
- **Not Personal**: Should not contain your name or email
- **Not Recent**: Cannot be one of your last 5 passwords

## Step-by-Step Guide

### Task 1: Changing Your Password (While Logged In)

1. **Log in to your account**
   - Use your current credentials
   - **Expected Result**: You're logged into your dashboard

2. **Navigate to security settings**
   - Click your profile icon in the top navigation
   - Select "Account Settings" or "Security Settings"
   - **Expected Result**: Settings page is displayed

3. **Locate password change section**
   - Find "Change Password" or "Password Settings"
   - Click "Change Password" button
   - **Expected Result**: Password change form appears

4. **Enter your current password**
   - Type your existing password for verification
   - This confirms you're the account owner
   - **Expected Result**: Current password field is filled

5. **Enter your new password**
   - Type your new password
   - Must meet all password requirements
   - Password strength indicator shows strength level
   - **Expected Result**: New password is entered and validated

6. **Confirm your new password**
   - Re-type your new password exactly
   - Must match the new password field
   - **Expected Result**: Confirmation password matches

7. **Review password requirements**
   - Check that all requirements are met (shown with checkmarks)
   - Requirements include:
     - ✓ At least 8 characters
     - ✓ Contains uppercase letter
     - ✓ Contains lowercase letter
     - ✓ Contains number
     - ✓ Contains special character
   - **Expected Result**: All requirements are satisfied

8. **Submit the password change**
   - Click "Change Password" or "Update Password" button
   - **Expected Result**: Password is updated

9. **Receive confirmation**
   - You see a success message: "Password changed successfully"
   - You may receive a confirmation email
   - **Expected Result**: Password is now active

10. **Log in with new password**
    - You may be logged out automatically
    - Log back in using your new password
    - **Expected Result**: Can access account with new credentials

### Task 2: Resetting Your Password (When Forgotten)

#### Step 1: Request Password Reset

1. **Navigate to the login page**
   - Go to `/accounts/login/`
   - **Expected Result**: Login form is displayed

2. **Click "Forgot Password?" link**
   - Usually located below the password field
   - **Expected Result**: Password reset email form appears

3. **Enter your email address**
   - Type the email you used during registration
   - Must be the email associated with your account
   - **Expected Result**: Email field is filled

4. **Submit the request**
   - Click "Send Reset Code" or "Reset Password" button
   - **Expected Result**: Request is submitted

5. **Receive confirmation message**
   - You see: "If an account exists with this email, you will receive a password reset code"
   - This prevents email enumeration attacks
   - **Expected Result**: Confirmation message is displayed

#### Step 2: Verify Email with OTP Code

1. **Check your email inbox**
   - Look for email from NORSU Alumni System
   - Subject: "Password Reset Code" or similar
   - **Expected Result**: Email arrives within a few minutes

2. **If you don't see the email**
   - Check spam/junk folder
   - Wait a few minutes and refresh
   - Verify you entered the correct email
   - **Expected Result**: Email is found

3. **Open the password reset email**
   - **Email contains**:
     - 6-digit verification code
     - Code expiration time (15 minutes)
     - Instructions
     - Security notice
   - **Expected Result**: Email opens successfully

4. **Copy the verification code**
   - The code is 6 digits (e.g., 123456)
   - Code is valid for 15 minutes
   - **Expected Result**: Code is copied or memorized

5. **Return to the password reset page**
   - You should be on the OTP verification page
   - Or navigate to `/accounts/password-reset-otp/`
   - **Expected Result**: OTP entry form is displayed

6. **Enter your email address**
   - Type the same email you used in step 1
   - **Expected Result**: Email field is filled

7. **Enter the verification code**
   - Type or paste the 6-digit code from email
   - Code must be entered within 15 minutes
   - **Expected Result**: Code is entered

8. **Submit the verification code**
   - Click "Verify Code" or "Continue" button
   - **Expected Result**: Code is verified

9. **Receive verification confirmation**
   - You see: "Email verified successfully"
   - You're redirected to set new password
   - **Expected Result**: New password form appears

#### Step 3: Set New Password

1. **Enter your new password**
   - Type your new password
   - Must meet all password requirements
   - Password strength indicator shows strength
   - **Expected Result**: New password is entered

2. **Confirm your new password**
   - Re-type your new password exactly
   - Must match the new password field
   - **Expected Result**: Passwords match

3. **Review password requirements**
   - Ensure all requirements are met
   - Check for green checkmarks next to each requirement
   - **Expected Result**: All requirements satisfied

4. **Submit your new password**
   - Click "Reset Password" or "Set New Password" button
   - **Expected Result**: Password is updated

5. **Receive success confirmation**
   - You see: "Password reset successfully!"
   - You're redirected to the login page
   - **Expected Result**: Success message is displayed

6. **Log in with new password**
   - Enter your email and new password
   - **Expected Result**: Successfully logged in

### Task 3: Resending Password Reset Code

If your verification code expires or you don't receive it:

1. **On the OTP verification page**
   - Look for "Resend Code" or "Didn't receive code?" link
   - **Expected Result**: Resend option is visible

2. **Wait for countdown timer (if present)**
   - You may need to wait 60 seconds between resend attempts
   - Timer shows remaining time
   - **Expected Result**: Timer counts down

3. **Click "Resend Code" button**
   - **Expected Result**: New code is sent

4. **Check your email for new code**
   - A new 6-digit code is sent
   - Previous code is invalidated
   - **Expected Result**: New email arrives

5. **Enter the new code**
   - Use the most recent code received
   - **Expected Result**: Verification succeeds

## Tips and Best Practices

### Creating Strong Passwords

- **Use a Passphrase**: Combine multiple words (e.g., "Coffee!Morning@2024")
- **Avoid Personal Information**: Don't use birthdays, names, or common words
- **Use Password Managers**: Let a password manager generate and store complex passwords
- **Make it Memorable**: Use a system you can remember but others can't guess
- **Unique for Each Site**: Don't reuse passwords across different websites

### Password Security

- **Change Regularly**: Update your password every 3-6 months
- **Don't Share**: Never share your password with anyone
- **Avoid Writing Down**: Don't write passwords on paper or in plain text files
- **Use Two-Factor Authentication**: Enable if available for extra security
- **Be Wary of Phishing**: Only enter password on official NORSU Alumni System pages

### When to Change Your Password

- **Suspected Compromise**: If you think someone knows your password
- **After Shared Device Use**: If you logged in on a public computer
- **Regular Maintenance**: Every 3-6 months as good practice
- **Security Breach**: If notified of a security incident
- **Weak Password**: If your current password doesn't meet best practices

## Common Use Cases

### Use Case 1: Routine Password Update
- Change password every 3-6 months for security
- Use the "Change Password" feature while logged in
- Choose a strong, unique password

### Use Case 2: Forgotten Password
- Use "Forgot Password" on login page
- Verify identity via email code
- Set a new password you'll remember

### Use Case 3: Suspected Account Compromise
- Immediately change password if you suspect unauthorized access
- Review recent account activity
- Contact administrators if you see suspicious activity

### Use Case 4: Password Doesn't Meet Requirements
- System may require password update if old password is weak
- Follow password change process
- Ensure new password meets all requirements

## Troubleshooting

### Issue: Current password not accepted when changing
**Symptoms**: "Incorrect password" error when trying to change password

**Solution**:
- Verify you're entering the correct current password
- Check that Caps Lock is off
- Try copying and pasting if you have it saved
- If you've forgotten current password, use "Forgot Password" instead
- Log out and log back in to verify current password
- Contact support if you're certain password is correct

### Issue: New password doesn't meet requirements
**Symptoms**: Cannot submit new password, requirements shown in red

**Solution**:
- Review each requirement carefully
- Ensure password has:
  - At least 8 characters
  - One uppercase letter (A-Z)
  - One lowercase letter (a-z)
  - One number (0-9)
  - One special character (!@#$%^&*)
- Try a password generator for a strong password
- Check that password isn't too common

### Issue: Password reset email not received
**Symptoms**: No email after requesting password reset

**Solution**:
- Check spam/junk folder
- Wait 5-10 minutes (email may be delayed)
- Verify you entered correct email address
- Check if email provider is blocking emails
- Try resending the code
- Contact support if email never arrives

### Issue: Verification code expired
**Symptoms**: "Code expired" error when entering OTP

**Solution**:
- Codes expire after 15 minutes for security
- Click "Resend Code" to get a new code
- Enter the new code promptly
- Complete the process within 15 minutes

### Issue: Verification code not working
**Symptoms**: "Invalid code" error

**Solution**:
- Ensure you're using the most recent code
- Check for typos (codes are case-sensitive)
- Verify you're entering all 6 digits
- Make sure code hasn't expired (15 minutes)
- Request a new code if needed
- Copy and paste code to avoid typos

### Issue: "Password recently used" error
**Symptoms**: Cannot use new password because it was used before

**Solution**:
- System prevents reusing last 5 passwords
- Choose a completely different password
- Don't just add a number to old password
- Create a unique, new password

### Issue: Too many password reset attempts
**Symptoms**: "Too many attempts" error message

**Solution**:
- Rate limiting prevents abuse (3 attempts per 15 minutes)
- Wait 15-30 minutes before trying again
- Ensure you're using correct email address
- Contact support if you need immediate access

### Issue: Logged out after password change
**Symptoms**: Automatically logged out after changing password

**Solution**:
- This is normal security behavior
- Simply log back in with your new password
- Verifies that new password works correctly
- All other sessions are terminated for security

### Issue: Password change confirmation email not received
**Symptoms**: Changed password but no confirmation email

**Solution**:
- Check spam/junk folder
- Confirmation emails may be delayed
- Password change is still successful even without email
- Try logging in with new password to verify
- Contact support if concerned about security

## Security Features

### Password Encryption
- **Hashing**: Passwords are hashed, never stored in plain text
- **Salt**: Unique salt added to each password
- **Secure Algorithm**: Uses industry-standard bcrypt or similar
- **No Recovery**: Even administrators cannot see your password

### Verification Process
- **Email Verification**: Confirms identity via email
- **Time-Limited Codes**: Codes expire after 15 minutes
- **One-Time Use**: Each code can only be used once
- **Rate Limiting**: Prevents brute force attacks

### Password History
- **Tracks Last 5 Passwords**: Prevents immediate reuse
- **Encourages Variety**: Forces creation of new passwords
- **Security Compliance**: Meets security best practices

### Audit Logging
- **All Changes Logged**: Password changes are recorded
- **IP Address Tracked**: Logs where change originated
- **Timestamp Recorded**: When change occurred
- **Security Monitoring**: Helps detect unauthorized changes

## What Happens After Password Change

Once you change your password:

1. **Old Password Invalidated**: Previous password no longer works
2. **All Sessions Terminated**: Logged out from all devices
3. **Confirmation Email Sent**: You receive email notification
4. **Password History Updated**: New password added to history
5. **Security Log Created**: Change is recorded for audit
6. **Must Re-Login**: Need to log in with new password

## What Happens After Password Reset

After resetting your password:

1. **New Password Active**: Can log in with new password
2. **Old Password Invalidated**: Previous password no longer works
3. **Verification Code Invalidated**: Used code cannot be reused
4. **All Sessions Terminated**: Logged out from all devices
5. **Confirmation Email Sent**: You receive email notification
6. **Security Alert**: May receive security notification email

## Related Features

- [Login and Logout](login-logout.md) - Access your account
- [Email Verification](email-verification.md) - Verify your email address
- [Security Dashboard](security-dashboard.md) - View account security information
- [Account Settings](../profile-management/README.md) - Manage account preferences

## Additional Notes

### Password Reset Limits
- **3 attempts per 15 minutes**: Prevents abuse
- **Code valid for 15 minutes**: Must complete process promptly
- **One active code at a time**: New code invalidates previous

### Email Delivery
- **Usually instant**: Emails typically arrive within 1-2 minutes
- **Check spam**: May be filtered as spam
- **Provider delays**: Some email providers may delay delivery
- **Contact support**: If emails consistently don't arrive

### Browser Compatibility
- Works with all modern browsers
- JavaScript must be enabled
- Cookies must be enabled for session management
- Recommended to use latest browser version

### Mobile Access
- Fully responsive on mobile devices
- Same process on mobile as desktop
- Touch-friendly interface
- Can copy/paste codes on mobile

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the [Troubleshooting Guide](../../resources/troubleshooting.md).

*Last Updated: November 19, 2025*
