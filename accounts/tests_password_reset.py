"""
Tests for password reset functionality
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from accounts.security import SecurityCodeManager
import re

User = get_user_model()


class PasswordResetFlowTest(TestCase):
    """Test the complete password reset flow"""
    
    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='OldPassword123!',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        self.email = 'testuser@example.com'
    
    def test_password_reset_email_page_loads(self):
        """Test that password reset email page loads correctly"""
        response = self.client.get(reverse('accounts:password_reset_email'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset Password')
        self.assertContains(response, 'email')
    
    def test_password_reset_email_request(self):
        """Test requesting password reset email"""
        response = self.client.post(
            reverse('accounts:password_reset_email'),
            {'email': self.email}
        )
        
        # Should redirect to OTP page
        self.assertEqual(response.status_code, 302)
        self.assertIn('password-reset-otp', response.url)
        
        # Check that email was sent (in test mode, emails are stored in mail.outbox)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Code', mail.outbox[0].subject)
        self.assertIn(self.email, mail.outbox[0].to)
    
    def test_password_reset_otp_page_loads(self):
        """Test that OTP verification page loads correctly"""
        response = self.client.get(reverse('accounts:password_reset_otp'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Verify Your Email')
        self.assertContains(response, 'verification_code')
    
    def test_password_reset_with_valid_code(self):
        """Test password reset with valid verification code"""
        # Step 1: Request password reset
        self.client.post(
            reverse('accounts:password_reset_email'),
            {'email': self.email}
        )
        
        # Extract verification code from email
        email_body = mail.outbox[0].body
        code_match = re.search(r'Code:\s*(\d{6})', email_body)
        self.assertIsNotNone(code_match, "Verification code not found in email")
        verification_code = code_match.group(1)
        
        # Step 2: Verify code
        response = self.client.post(
            reverse('accounts:password_reset_otp'),
            {
                'email': self.email,
                'verification_code': verification_code
            }
        )
        
        # Should redirect to new password page
        self.assertEqual(response.status_code, 302)
        self.assertIn('password-reset-new-password', response.url)
        
        # Check that email is stored in session
        self.assertEqual(self.client.session.get('password_reset_email'), self.email)
    
    def test_password_reset_with_invalid_code(self):
        """Test password reset with invalid verification code"""
        # Request password reset first
        self.client.post(
            reverse('accounts:password_reset_email'),
            {'email': self.email}
        )
        
        # Try with invalid code
        response = self.client.post(
            reverse('accounts:password_reset_otp'),
            {
                'email': self.email,
                'verification_code': '000000'
            }
        )
        
        # Should stay on same page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')
    
    def test_password_reset_new_password_page_requires_session(self):
        """Test that new password page requires valid session"""
        response = self.client.get(reverse('accounts:password_reset_new_password'))
        
        # Should redirect to email page if no session
        self.assertEqual(response.status_code, 302)
        self.assertIn('password-reset-email', response.url)
    
    def test_complete_password_reset_flow(self):
        """Test the complete password reset flow"""
        # Step 1: Request password reset
        response = self.client.post(
            reverse('accounts:password_reset_email'),
            {'email': self.email}
        )
        self.assertEqual(response.status_code, 302)
        
        # Extract verification code
        email_body = mail.outbox[0].body
        code_match = re.search(r'Code:\s*(\d{6})', email_body)
        verification_code = code_match.group(1)
        
        # Step 2: Verify code
        response = self.client.post(
            reverse('accounts:password_reset_otp'),
            {
                'email': self.email,
                'verification_code': verification_code
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 3: Set new password
        new_password = 'NewPassword123!'
        response = self.client.post(
            reverse('accounts:password_reset_new_password'),
            {
                'new_password1': new_password,
                'new_password2': new_password
            }
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Step 4: Verify can login with new password
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        
        # Try logging in
        login_success = self.client.login(
            username=self.email,
            password=new_password
        )
        self.assertTrue(login_success)
    
    def test_password_reset_with_weak_password(self):
        """Test that weak passwords are rejected"""
        # Set up session
        session = self.client.session
        session['password_reset_email'] = self.email
        session.save()
        
        # Try with weak password
        response = self.client.post(
            reverse('accounts:password_reset_new_password'),
            {
                'new_password1': 'weak',
                'new_password2': 'weak'
            }
        )
        
        # Should stay on same page with error
        self.assertEqual(response.status_code, 200)
        # Form should have errors
        self.assertTrue(response.context['form'].errors)
    
    def test_password_reset_with_mismatched_passwords(self):
        """Test that mismatched passwords are rejected"""
        # Set up session
        session = self.client.session
        session['password_reset_email'] = self.email
        session.save()
        
        # Try with mismatched passwords
        response = self.client.post(
            reverse('accounts:password_reset_new_password'),
            {
                'new_password1': 'NewPassword123!',
                'new_password2': 'DifferentPassword123!'
            }
        )
        
        # Should stay on same page with error
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
    
    def test_password_reset_rate_limiting(self):
        """Test that rate limiting works"""
        # Make 3 requests (should succeed)
        for i in range(3):
            response = self.client.post(
                reverse('accounts:password_reset_email'),
                {'email': self.email}
            )
            self.assertEqual(response.status_code, 302)
        
        # 4th request should be rate limited
        response = self.client.post(
            reverse('accounts:password_reset_email'),
            {'email': self.email}
        )
        
        # Should stay on same page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many')
    
    def test_password_reset_with_nonexistent_email(self):
        """Test password reset with non-existent email (should show clear error)"""
        response = self.client.post(
            reverse('accounts:password_reset_email'),
            {'email': 'nonexistent@example.com'}
        )
        
        # Should stay on same page with error message
        self.assertEqual(response.status_code, 200)
        
        # Should show clear error that email is not registered
        messages_list = list(response.context['messages'])
        self.assertTrue(any('not registered' in str(m).lower() for m in messages_list))
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)


class SecurityCodeManagerTest(TestCase):
    """Test the SecurityCodeManager"""
    
    def test_generate_code(self):
        """Test code generation"""
        code = SecurityCodeManager.generate_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_store_and_verify_code(self):
        """Test storing and verifying codes"""
        email = 'test@example.com'
        code = SecurityCodeManager.generate_code()
        
        # Store code
        SecurityCodeManager.store_code(email, code, 'password_reset')
        
        # Verify code
        is_valid, message = SecurityCodeManager.verify_code(email, code, 'password_reset')
        self.assertTrue(is_valid)
        self.assertEqual(message, 'Code verified successfully')
    
    def test_verify_invalid_code(self):
        """Test verifying invalid code"""
        email = 'test@example.com'
        code = SecurityCodeManager.generate_code()
        
        # Store code
        SecurityCodeManager.store_code(email, code, 'password_reset')
        
        # Try to verify with wrong code
        is_valid, message = SecurityCodeManager.verify_code(email, '000000', 'password_reset')
        self.assertFalse(is_valid)
        self.assertIn('Invalid', message)
    
    def test_verify_expired_code(self):
        """Test verifying expired code"""
        from django.core.cache import cache
        from django.utils import timezone
        from datetime import timedelta
        
        email = 'test@example.com'
        code = SecurityCodeManager.generate_code()
        
        # Store code with past expiration
        cache_key = f'verification_code_{email}_password_reset'
        cache.set(cache_key, {
            'code': code,
            'expires_at': (timezone.now() - timedelta(minutes=1)).isoformat()
        }, timeout=900)
        
        # Try to verify
        is_valid, message = SecurityCodeManager.verify_code(email, code, 'password_reset')
        self.assertFalse(is_valid)
        self.assertIn('expired', message.lower())
