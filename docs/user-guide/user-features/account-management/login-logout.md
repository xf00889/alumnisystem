# Login Logout

## Overview

The Login and Logout features allow you to securely access your NORSU Alumni System account and exit when you're done. The system includes security features like reCAPTCHA protection and a "Remember Me" option for trusted devices.

## Who Can Use This Feature

- **All registered users** with verified email addresses
- **Users who have completed the registration process**
- **Alumni who need to access their account**

## Prerequisites

- Registered account with verified email address
- Valid email and password credentials
- Internet connection and web browser

## How to Access

### Login Page
1. Navigate to the NORSU Alumni System website
2. Click "Login" or "Sign In" in the navigation menu
3. Or visit: `/accounts/login/`

### Logout
1. Click on your profile icon or name in the top navigation
2. Select "Logout" from the dropdown menu

## Key Features

- **Secure Authentication**: Password-protected access to your account
- **reCAPTCHA Protection**: Prevents automated login attempts
- **Remember Me**: Stay logged in on trusted devices
- **Session Management**: Automatic logout after inactivity
- **Error Handling**: Clear messages for login issues

## Step-by-Step Guide

### Task 1: Logging In

1. **Navigate to the login page**
   - Click "Login" in the main navigation
   - Or go directly to `/accounts/login/`
   - **Expected Result**: Login form is displayed

2. **Enter your email address**
   - Type the email you used during registration
   - Email must be verified to log in
   - **Expected Result**: Email field is filled

3. **Enter your password**
   - Type your account password
   - Password is case-sensitive
   - **Expected Result**: Password is entered (shown as dots or asterisks)

4. **Complete reCAPTCHA verification (if enabled)**
   - Check the "I'm not a robot" box
   - Complete any additional verification steps if prompted
   - **Expected Result**: reCAPTCHA is verified

5. **Choose "Remember Me" option (optional)**
   - Check the "Remember Me" box to stay logged in
   - Only use this on your personal, secure devices
   - **Expected Result**: Option is selected

6. **Click "Sign In" or "Login" button**
   - **Expected Result**: You're logged into your account

7. **Access your dashboard**
   - You're redirected to the authenticated home page
   - You see your personalized dashboard
   - **Expected Result**: Dashboard displays with your information

### Task 2: Using "Remember Me" Feature

The "Remember Me" feature keeps you logged in on trusted devices so you don't have to enter your credentials every time.

1. **When to use "Remember Me"**
   - On your personal computer or device
   - On devices you trust and control
   - When you're the only user of the device
   - **Expected Result**: Convenient access without repeated logins

2. **When NOT to use "Remember Me"**
   - On public computers (libraries, internet cafes)
   - On shared devices (family computers, work stations)
   - On borrowed devices
   - **Expected Result**: Better security on shared devices

3. **How "Remember Me" works**
   - Extends your session duration (typically 2 weeks)
   - Keeps you logged in even after closing the browser
   - Session expires after the set duration
   - **Expected Result**: Automatic login on return visits

4. **Disabling "Remember Me"**
   - Simply log out manually
   - Clear your browser cookies
   - The session will expire automatically after the duration
   - **Expected Result**: You'll need to log in again next time

### Task 3: Logging Out

1. **Locate the logout option**
   - Look for your profile icon or name in the top navigation bar
   - Usually in the top-right corner of the page
   - **Expected Result**: Profile menu is visible

2. **Click on your profile icon/name**
   - A dropdown menu appears
   - **Expected Result**: Menu shows account options

3. **Select "Logout" or "Sign Out"**
   - Click the logout option in the dropdown
   - **Expected Result**: You're logged out immediately

4. **Confirm logout**
   - You're redirected to the public home page or login page
   - You see a confirmation message: "You have been logged out"
   - **Expected Result**: You're no longer authenticated

5. **Verify logout**
   - Try accessing a protected page
   - You should be redirected to the login page
   - **Expected Result**: Cannot access authenticated features

### Task 4: Handling Login Issues

1. **If you see "Invalid credentials" error**
   - Double-check your email address
   - Verify your password (check Caps Lock)
   - Try the "Forgot Password" link if needed
   - **Expected Result**: Successful login with correct credentials

2. **If you see "Email not verified" error**
   - Check your email for verification link
   - Click "Resend Verification Email" if needed
   - Complete email verification process
   - **Expected Result**: Can log in after verification

3. **If you see "Account inactive" error**
   - Your account may be deactivated
   - Contact system administrators
   - **Expected Result**: Administrator assistance

4. **If reCAPTCHA fails**
   - Refresh the page and try again
   - Ensure JavaScript is enabled
   - Try a different browser
   - **Expected Result**: reCAPTCHA verification succeeds

## Tips and Best Practices

- **Use Strong Passwords**: Create a unique, complex password for your account
- **Log Out on Shared Devices**: Always log out when using public or shared computers
- **Don't Save Passwords on Public Devices**: Decline browser password save prompts on shared computers
- **Check the URL**: Ensure you're on the official NORSU Alumni System website
- **Keep Credentials Private**: Never share your login information with anyone
- **Use Password Managers**: Consider using a password manager for secure credential storage
- **Monitor Login Activity**: Check for any suspicious login attempts
- **Update Browser**: Keep your web browser up to date for security

## Common Use Cases

### Use Case 1: Daily Access on Personal Device
- Use "Remember Me" for convenience
- You'll stay logged in for up to 2 weeks
- No need to enter credentials each time

### Use Case 2: Access on Public Computer
- Do NOT use "Remember Me"
- Always log out when finished
- Clear browser history if possible

### Use Case 3: Multiple Device Access
- You can be logged in on multiple devices simultaneously
- Each device maintains its own session
- Logging out on one device doesn't affect others

### Use Case 4: Forgotten Password
- Use the "Forgot Password" link on the login page
- Follow the password reset process
- See [Password Management](password-management.md) for details

## Troubleshooting

### Issue: Cannot log in with correct credentials
**Symptoms**: Login fails even with correct email and password

**Solution**:
- Verify your email address is correct
- Check that Caps Lock is off
- Ensure your email is verified (check inbox for verification email)
- Try resetting your password using "Forgot Password"
- Clear browser cache and cookies
- Try a different browser
- Contact support if issue persists

### Issue: "Remember Me" not working
**Symptoms**: Have to log in every time despite checking "Remember Me"

**Solution**:
- Check browser cookie settings (cookies must be enabled)
- Ensure you're not in private/incognito mode
- Check if browser is set to clear cookies on exit
- Try a different browser
- Disable browser extensions that might block cookies

### Issue: Automatically logged out too quickly
**Symptoms**: Session expires unexpectedly

**Solution**:
- This is a security feature for inactive sessions
- Use "Remember Me" to extend session duration
- Check if you're on a shared/public computer (shorter sessions)
- Ensure stable internet connection
- Contact administrators if sessions are too short

### Issue: reCAPTCHA not loading
**Symptoms**: Cannot complete reCAPTCHA verification

**Solution**:
- Ensure JavaScript is enabled in your browser
- Disable ad blockers or privacy extensions temporarily
- Check your internet connection
- Try a different browser
- Clear browser cache
- Contact support if reCAPTCHA is consistently failing

### Issue: Redirected to wrong page after login
**Symptoms**: Don't see expected page after logging in

**Solution**:
- Check if you need to complete post-registration profile
- Verify your account is fully activated
- Clear browser cache
- Try logging out and back in
- Contact support if redirected to error page

### Issue: Account locked after multiple failed attempts
**Symptoms**: Cannot log in after several wrong password attempts

**Solution**:
- Wait 15-30 minutes before trying again (rate limiting)
- Use "Forgot Password" to reset your password
- Contact administrators if you believe account is compromised
- Check email for security notifications

### Issue: Session expired message
**Symptoms**: See "Your session has expired" message

**Solution**:
- This is normal after inactivity or session timeout
- Simply log in again
- Use "Remember Me" for longer sessions
- Save your work frequently to avoid data loss

## Security Features

### Session Management
- **Automatic Timeout**: Sessions expire after period of inactivity
- **Secure Cookies**: Session data is encrypted
- **HTTPS**: All login traffic is encrypted
- **Session Validation**: Each request validates session integrity

### Login Protection
- **reCAPTCHA**: Prevents automated bot attacks
- **Rate Limiting**: Limits failed login attempts
- **Account Lockout**: Temporary lockout after multiple failures
- **Audit Logging**: All login attempts are logged

### Password Security
- **Encrypted Storage**: Passwords are never stored in plain text
- **Secure Transmission**: Passwords sent over encrypted connection
- **Strength Requirements**: Enforces strong password policies
- **No Password Display**: Passwords shown as dots/asterisks

## What Happens After Login

Once you successfully log in:

1. **Session Created**: A secure session is established
2. **Dashboard Access**: You're redirected to your personalized dashboard
3. **Feature Access**: All authenticated features become available
4. **Profile Loaded**: Your profile information is loaded
5. **Notifications**: You see any pending notifications
6. **Activity Tracked**: Your login is recorded for security

## What Happens After Logout

When you log out:

1. **Session Terminated**: Your session is immediately ended
2. **Cookies Cleared**: Session cookies are removed
3. **Redirect**: You're sent to the public home page
4. **Access Revoked**: Cannot access authenticated features
5. **Activity Logged**: Logout is recorded for security

## Related Features

- [Password Management](password-management.md) - Change or reset your password
- [Email Verification](email-verification.md) - Verify your email address
- [Registration Process](../../public-features/registration.md) - Create a new account
- [Profile Management](../profile-management/README.md) - Update your profile information
- [Security Dashboard](security-dashboard.md) - View account security information

## Additional Notes

### Session Duration
- **Without "Remember Me"**: Session lasts until browser is closed or after 30 minutes of inactivity
- **With "Remember Me"**: Session lasts up to 2 weeks
- **Security Timeout**: Automatic logout after extended inactivity

### Browser Compatibility
- Works with all modern browsers (Chrome, Firefox, Safari, Edge)
- JavaScript must be enabled
- Cookies must be enabled
- Recommended to use latest browser version

### Mobile Access
- Fully responsive on mobile devices
- Same login process on mobile
- Touch-friendly interface
- Mobile sessions managed same as desktop

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the [Troubleshooting Guide](../../resources/troubleshooting.md).

*Last Updated: November 19, 2025*
