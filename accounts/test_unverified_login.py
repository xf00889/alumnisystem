"""
Tests for unverified user login redirect feature
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages

User = get_user_model()


class UnverifiedUserLoginRedirectTest(TestCase):
    """Test that unverified users are redirected to email verification page when trying to login"""
    
    def setUp(self):
        """Set up test client and create test user"""
        self.client = Client()
        self.email = 'test@example.com'
        self.password = 'TestPassword123!'
        
        # Create unverified user (is_active=False)
        self.user = User.objects.create_user(
            username='testuser',
            email=self.email,
            password=self.password,
            is_active=False  # Unverified user
        )
    
    def test_unverified_user_redirected_to_verification(self):
        """Test that unverified user is redirected to email verification page"""
        # Attempt to login with unverified account
        response = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        # Check that user was redirected to verification page
        self.assertRedirects(
            response,
            f'/accounts/verify-email/?email={self.email}',
            status_code=302,
            target_status_code=200
        )
        
        # Check that appropriate message was shown
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(m) for m in messages]
        
        # Should have warning message about unverified email
        self.assertTrue(
            any('not been verified' in msg.lower() for msg in message_texts),
            f"Expected warning message about unverified email. Got: {message_texts}"
        )
    
    def test_verified_user_not_redirected(self):
        """Test that verified user is NOT redirected to verification page"""
        # Activate the user (verify email)
        self.user.is_active = True
        self.user.save()
        
        # Attempt to login with verified account
        response = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        # Check that user was NOT redirected to verification page
        self.assertNotIn('/accounts/verify-email/', response.redirect_chain[0][0])
        
        # User should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.email, self.email)
    
    def test_wrong_password_not_redirected(self):
        """Test that wrong password does NOT redirect to verification page"""
        # Attempt to login with wrong password
        response = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': 'WrongPassword123!',
        }, follow=True)
        
        # Check that user was NOT redirected to verification page
        # Should stay on login page with error message
        self.assertEqual(response.status_code, 200)
        
        # Check for error message (not verification redirect)
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(m) for m in messages]
        
        # Should have error message about invalid credentials
        # NOT a message about verification
        self.assertFalse(
            any('verify' in msg.lower() for msg in message_texts),
            f"Should not mention verification for wrong password. Got: {message_texts}"
        )
    
    def test_nonexistent_user_not_redirected(self):
        """Test that non-existent user does NOT redirect to verification page"""
        # Attempt to login with non-existent email
        response = self.client.post(reverse('account_login'), {
            'login': 'nonexistent@example.com',
            'password': 'SomePassword123!',
        }, follow=True)
        
        # Check that user was NOT redirected to verification page
        self.assertEqual(response.status_code, 200)
        
        # Should stay on login page with error message
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(m) for m in messages]
        
        # Should have error message about invalid credentials
        # NOT a message about verification
        self.assertFalse(
            any('verify' in msg.lower() for msg in message_texts),
            f"Should not mention verification for non-existent user. Got: {message_texts}"
        )
    
    def test_email_prefilled_on_verification_page(self):
        """Test that email is pre-filled on verification page after redirect"""
        # Attempt to login with unverified account
        response = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        # Check that email parameter is in URL
        self.assertIn(f'email={self.email}', response.request['QUERY_STRING'])
        
        # Check that email is in context
        self.assertEqual(response.context.get('user_email'), self.email)
    
    def test_session_flag_set_on_redirect(self):
        """Test that session flag is set when redirecting unverified user"""
        # Attempt to login with unverified account
        response = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=False)  # Don't follow redirect
        
        # Check that session flag was set
        # Note: The flag is popped in the verify_email view, so we need to check before following
        session = self.client.session
        self.assertEqual(session.get('inactive_account_email'), self.email)
    
    def test_multiple_login_attempts_redirect_each_time(self):
        """Test that multiple login attempts by unverified user redirect each time"""
        # First login attempt
        response1 = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        self.assertIn('/accounts/verify-email/', response1.redirect_chain[0][0])
        
        # Second login attempt (go back to login page and try again)
        response2 = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        self.assertIn('/accounts/verify-email/', response2.redirect_chain[0][0])
        
        # Third login attempt
        response3 = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        self.assertIn('/accounts/verify-email/', response3.redirect_chain[0][0])


class VerificationPageMessagesTest(TestCase):
    """Test that verification page shows appropriate messages for redirected users"""
    
    def setUp(self):
        """Set up test client and create test user"""
        self.client = Client()
        self.email = 'test@example.com'
        self.password = 'TestPassword123!'
        
        # Create unverified user
        self.user = User.objects.create_user(
            username='testuser',
            email=self.email,
            password=self.password,
            is_active=False
        )
    
    def test_info_message_shown_on_redirect(self):
        """Test that info message is shown when user is redirected from login"""
        # Attempt to login (will redirect to verification)
        response = self.client.post(reverse('account_login'), {
            'login': self.email,
            'password': self.password,
        }, follow=True)
        
        # Check for info message
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(m) for m in messages]
        
        # Should have info message about verifying to activate account
        self.assertTrue(
            any('verify your email address to activate your account' in msg.lower() for msg in message_texts),
            f"Expected info message about verification. Got: {message_texts}"
        )
    
    def test_direct_access_no_extra_message(self):
        """Test that direct access to verification page doesn't show redirect message"""
        # Access verification page directly (not from login redirect)
        response = self.client.get(f'/accounts/verify-email/?email={self.email}')
        
        # Check messages
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(m) for m in messages]
        
        # Should NOT have the "activate your account" message
        # (that's only for redirects from login)
        self.assertFalse(
            any('activate your account' in msg.lower() for msg in message_texts),
            f"Should not show redirect message for direct access. Got: {message_texts}"
        )


# Run tests with: python manage.py test accounts.test_unverified_login
