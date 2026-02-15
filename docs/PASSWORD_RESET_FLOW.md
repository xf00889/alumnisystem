# Password Reset Flow Documentation

## Overview
The password reset functionality provides a secure, multi-step process for users to reset their passwords using email verification codes.

## Complete Flow

### Step 1: Request Password Reset
**URL:** `/accounts/password-reset-email/`
**View:** `password_reset_email`
**Template:** `templates/accounts/password_reset_email.html`

1. User clicks "Forgot Password" link on login page
2. User enters their email address
3. System validates email and checks rate limiting (3 attempts per 15 minutes)
4. If valid, generates a 6-digit verification code
5. Sends verification code to user's email
6. Redirects to OTP verification page

**Security Features:**
- Rate limiting (3 attempts per 15 minutes)
- Email validation (checks if email exists in system)
- reCAPTCHA protection (if enabled)
- Security audit logging

**Note:** The system will now explicitly tell users if their email is not registered, rather than using a generic message. This improves user experience while still maintaining security through rate limiting and audit logging.

### Step 2: Verify Code
**URL:** `/accounts/password-reset-otp/`
**View:** `password_reset_otp`
**Template:** `templates/accounts/password_reset_otp.html`

1. User enters their email address
2. User enters the 6-digit verification code received via email
3. System verifies the code (expires after 15 minutes)
4. If valid, stores email in session and redirects to password change page
5. If invalid, shows error message

**Features:**
- Code expiration (15 minutes)
- Resend code functionality with countdown timer
- Rate limiting on resend attempts
- reCAPTCHA protection (if enabled)

**Resend Functionality:**
- User can request a new code if they didn't receive it
- Rate limited to prevent abuse
- Countdown timer shows when next resend is available

### Step 3: Set New Password
**URL:** `/accounts/password-reset-new-password/`
**View:** `password_reset_new_password`
**Template:** `templates/accounts/password_reset_new_password.html`

1. User enters new password
2. User confirms new password
3. System validates password strength:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character
4. System checks password history (prevents reuse of recent passwords)
5. If valid, updates password and redirects to login page

**Security Features:**
- Password strength validation
- Password history checking
- Password match validation
- Session expiry (15 minutes)
- reCAPTCHA protection (if enabled)
- Real-time password strength indicator

### Step 4: Login with New Password
**URL:** `/accounts/login/`

1. User is redirected to login page with success message
2. User can now login with their new password

## API Endpoints

### Resend Password Reset OTP
**URL:** `/accounts/resend-password-reset-otp/`
**Method:** POST
**Parameters:** `email`
**Response:** JSON with success/error message

### Check Password Reset Countdown
**URL:** `/accounts/check-password-reset-countdown/`
**Method:** POST
**Parameters:** `email`
**Response:** JSON with countdown status

## Forms

### PasswordResetEmailForm
- **Fields:** email, captcha (optional)
- **Validation:** Email format, rate limiting

### PasswordResetOTPForm
- **Fields:** email, verification_code, captcha (optional)
- **Validation:** 6-digit numeric code, email format

### PasswordResetNewPasswordForm
- **Fields:** new_password1, new_password2, captcha (optional)
- **Validation:** Password strength, password match, password history

## Security Features

1. **Rate Limiting**
   - 3 password reset attempts per 15 minutes per email
   - Prevents brute force attacks

2. **Email Validation**
   - Checks if email exists in system before sending code
   - Clear error message if email not registered
   - Prevents wasted emails and improves UX

3. **Code Expiration**
   - Verification codes expire after 15 minutes
   - Prevents replay attacks

4. **Session Security**
   - Password reset session expires after 15 minutes
   - Prevents session hijacking

5. **Password Validation**
   - Strong password requirements
   - Password history checking
   - Real-time strength indicator

6. **Audit Logging**
   - All password reset attempts are logged
   - Failed attempts are tracked
   - Security events are recorded

7. **reCAPTCHA Protection**
   - Optional reCAPTCHA on all forms
   - Prevents automated attacks

## Email Templates

### Password Reset Email
**Template:** `templates/emails/password_reset_verification.html`
**Subject:** "NORSU Alumni - Password Reset Code"

Contains:
- Verification code
- Expiration time (15 minutes)
- Security notice

## Error Handling

### Common Errors

1. **Email Not Registered**
   - Message: "This email address is not registered in our system. Please check your email or sign up for a new account."
   - Action: User should verify email or create new account

2. **Rate Limit Exceeded**
   - Message: "Too many password reset attempts. Please try again later."
   - Shows remaining time

3. **Invalid/Expired Code**
   - Message: "Invalid or expired verification code."
   - Allows resend

4. **Session Expired**
   - Message: "Session expired. Please start the password reset process again."
   - Redirects to step 1

5. **Weak Password**
   - Message: "Your password is too weak. Please choose a stronger password."
   - Shows requirements

6. **Password Mismatch**
   - Message: "Passwords do not match."
   - Highlights fields

## Testing

### Manual Testing Steps

1. **Test Valid Flow:**
   ```
   1. Go to /accounts/password-reset-email/
   2. Enter valid email
   3. Check email for code
   4. Go to /accounts/password-reset-otp/
   5. Enter email and code
   6. Go to /accounts/password-reset-new-password/
   7. Enter new password (meeting requirements)
   8. Confirm password
   9. Verify redirect to login
   10. Login with new password
   ```

2. **Test Invalid Email:**
   ```
   1. Enter non-existent email
   2. Verify generic success message (security)
   3. Verify no email sent
   ```

3. **Test Rate Limiting:**
   ```
   1. Request password reset 3 times quickly
   2. Verify 4th attempt is blocked
   3. Wait 15 minutes
   4. Verify can request again
   ```

4. **Test Code Expiration:**
   ```
   1. Request password reset
   2. Wait 16 minutes
   3. Try to use code
   4. Verify "expired" error
   ```

5. **Test Weak Password:**
   ```
   1. Complete steps 1-2
   2. Enter weak password (e.g., "password")
   3. Verify validation error
   4. See strength indicator
   ```

6. **Test Resend Functionality:**
   ```
   1. Request password reset
   2. Go to OTP page
   3. Click "Resend Code"
   4. Verify new code sent
   5. Verify countdown timer
   ```

## Development Mode

In development mode (`DEBUG=True`):
- Verification codes are logged to console
- Email sending failures don't block the flow
- Additional debug logging is enabled

## Production Considerations

1. **Email Configuration**
   - Ensure SMTP settings are correct
   - Test email delivery
   - Monitor email bounce rates

2. **Rate Limiting**
   - Adjust limits based on usage patterns
   - Monitor for abuse

3. **Session Storage**
   - Use Redis for session storage in production
   - Set appropriate session timeouts

4. **Monitoring**
   - Monitor password reset attempts
   - Alert on suspicious patterns
   - Track success/failure rates

## Troubleshooting

### Email Not Received
1. Check spam folder
2. Verify email configuration
3. Check email service logs
4. Verify email address is correct

### Code Not Working
1. Check if code expired (15 minutes)
2. Verify correct email entered
3. Request new code
4. Check for typos

### Session Expired
1. Complete flow within 15 minutes
2. Don't close browser during process
3. Start over if session expires

## Related Files

- **Views:** `accounts/security_views.py`
- **Forms:** `accounts/forms.py`
- **URLs:** `accounts/urls.py`
- **Templates:** `templates/accounts/password_reset_*.html`
- **Email Templates:** `templates/emails/password_reset_verification.html`
- **Security:** `accounts/security.py`
- **Email Utils:** `accounts/email_utils.py`
