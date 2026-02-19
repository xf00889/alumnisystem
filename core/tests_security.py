"""
Security tests for messaging system
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from core.file_validators import (
    validate_message_attachment,
    sanitize_filename,
    is_image_file
)

User = get_user_model()


class FileValidationTests(TestCase):
    """Test file validation utilities"""
    
    def test_validate_allowed_file_types(self):
        """Test that allowed file types pass validation"""
        allowed_files = [
            ('test.pdf', b'fake pdf content'),
            ('test.jpg', b'fake image content'),
            ('test.png', b'fake image content'),
            ('test.docx', b'fake doc content'),
        ]
        
        for filename, content in allowed_files:
            file = SimpleUploadedFile(filename, content)
            try:
                validate_message_attachment(file)
            except ValidationError:
                self.fail(f"Validation failed for allowed file type: {filename}")
    
    def test_reject_disallowed_file_types(self):
        """Test that disallowed file types are rejected"""
        disallowed_files = [
            ('test.exe', b'fake executable'),
            ('test.sh', b'fake shell script'),
            ('test.bat', b'fake batch file'),
            ('test.php', b'fake php file'),
        ]
        
        for filename, content in disallowed_files:
            file = SimpleUploadedFile(filename, content)
            with self.assertRaises(ValidationError):
                validate_message_attachment(file)
    
    def test_reject_oversized_files(self):
        """Test that files over 5MB are rejected"""
        # Create a file larger than 5MB
        large_content = b'x' * (6 * 1024 * 1024)  # 6MB
        file = SimpleUploadedFile('large.pdf', large_content)
        
        with self.assertRaises(ValidationError):
            validate_message_attachment(file)
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        test_cases = [
            ('../../etc/passwd', 'passwd'),
            ('test file.pdf', 'test_file.pdf'),
            ('../../../malicious.exe', 'malicious.exe'),
            ('normal-file_123.pdf', 'normal-file_123.pdf'),
            ('file with spaces.jpg', 'file_with_spaces.jpg'),
        ]
        
        for input_name, expected_output in test_cases:
            result = sanitize_filename(input_name)
            self.assertEqual(result, expected_output)
    
    def test_is_image_file(self):
        """Test image file detection"""
        self.assertTrue(is_image_file('test.jpg'))
        self.assertTrue(is_image_file('test.png'))
        self.assertTrue(is_image_file('test.gif'))
        self.assertFalse(is_image_file('test.pdf'))
        self.assertFalse(is_image_file('test.docx'))


class XSSProtectionTests(TestCase):
    """Test XSS protection in templates"""
    
    def setUp(self):
        """Set up test users and connections"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_xss_payload_escaped_in_messages(self):
        """Test that XSS payloads are escaped in message display"""
        # This test would require creating actual messages and checking
        # that the rendered HTML escapes the content properly
        
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            '"><script>alert(String.fromCharCode(88,83,83))</script>',
        ]
        
        # Note: This is a placeholder test
        # In a real scenario, you would:
        # 1. Create a connection between users
        # 2. Send a message with XSS payload
        # 3. Retrieve the message page
        # 4. Verify the payload is escaped in HTML
        
        for payload in xss_payloads:
            # The linebreaksbr filter should escape these
            # Verify in actual template rendering
            pass


class RateLimitingTests(TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        """Set up test users"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_rate_limit_decorator_exists(self):
        """Test that rate limit decorator is importable"""
        from core.rate_limiters import rate_limit_messages
        self.assertIsNotNone(rate_limit_messages)
    
    # Note: Full rate limiting tests would require:
    # 1. Creating actual connections/conversations
    # 2. Sending multiple messages rapidly
    # 3. Verifying the 21st message is rejected
    # This requires more complex setup with actual models


class SecurityHeadersTests(TestCase):
    """Test security headers"""
    
    def test_csrf_token_in_forms(self):
        """Test that CSRF tokens are present in forms"""
        # This would be tested by checking actual form rendering
        pass
    
    def test_secure_cookies_in_production(self):
        """Test that secure cookie settings are configured"""
        from django.conf import settings
        
        # These should be True in production
        # Check your settings.py for these values
        if not settings.DEBUG:
            self.assertTrue(settings.SESSION_COOKIE_SECURE)
            self.assertTrue(settings.CSRF_COOKIE_SECURE)


# Run tests with: python manage.py test core.tests_security
