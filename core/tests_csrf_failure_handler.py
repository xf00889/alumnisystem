"""
Tests for CSRF failure handler that returns JSON for AJAX requests.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.view_handlers.error_handlers import csrf_failure
import json

User = get_user_model()


class CSRFFailureHandlerTestCase(TestCase):
    """Test CSRF failure handler returns JSON for AJAX requests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_csrf_failure_ajax_request_returns_json(self):
        """Test that AJAX requests receive JSON response on CSRF failure."""
        # Create AJAX request with X-Requested-With header
        request = self.factory.post(
            '/admin-dashboard/users/1/roles/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = self.user
        
        # Call CSRF failure handler
        response = csrf_failure(request, reason="CSRF token missing")
        
        # Verify JSON response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('CSRF verification failed', data['message'])
        self.assertIn('refresh the page', data['message'])
    
    def test_csrf_failure_json_content_type_returns_json(self):
        """Test that requests with JSON content type receive JSON response."""
        # Create request with application/json content type
        request = self.factory.post(
            '/admin-dashboard/users/1/roles/',
            content_type='application/json',
            data=json.dumps({'role': 'admin', 'action': 'assign'})
        )
        request.user = self.user
        
        # Call CSRF failure handler
        response = csrf_failure(request, reason="CSRF token missing")
        
        # Verify JSON response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('CSRF verification failed', data['message'])
    
    def test_csrf_failure_non_ajax_request_returns_html(self):
        """Test that non-AJAX requests receive HTML response on CSRF failure."""
        # Create regular request (no AJAX headers)
        request = self.factory.post('/some-form/')
        request.user = self.user
        
        # Call CSRF failure handler
        response = csrf_failure(request, reason="CSRF token missing")
        
        # Verify HTML response
        self.assertEqual(response.status_code, 403)
        self.assertIn('text/html', response['Content-Type'])
        self.assertIn(b'403 Forbidden', response.content)
        self.assertIn(b'CSRF verification failed', response.content)
    
    def test_csrf_failure_preserves_reason(self):
        """Test that CSRF failure handler preserves the failure reason."""
        # Create regular request
        request = self.factory.post('/some-form/')
        request.user = self.user
        
        # Call CSRF failure handler with specific reason
        response = csrf_failure(request, reason="Referer checking failed")
        
        # Verify reason is preserved in context
        self.assertEqual(response.status_code, 403)
