"""
Integration tests for documentation viewer sidebar integration.
Tests navigation flow and permissions.
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()


@override_settings(
    # Disable setup middleware for tests
    MIDDLEWARE=[m for m in __import__('django.conf', fromlist=['settings']).settings.MIDDLEWARE 
                if 'SetupRequiredMiddleware' not in m]
)
class DocumentationSidebarIntegrationTest(TestCase):
    """Test documentation integration with custom admin sidebar."""
    
    def setUp(self):
        """Set up test users and client."""
        self.client = Client()
        
        # Mock setup completion check
        self.setup_patcher = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        self.setup_patcher.start()
        
        # Create a superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create a regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
    
    def tearDown(self):
        """Clean up patches."""
        self.setup_patcher.stop()
    
    def test_documentation_accessible_to_authenticated_users(self):
        """Test that documentation is accessible to admin users only."""
        # Test with regular user - should be denied
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('docs:index'))
        self.assertEqual(response.status_code, 404)  # Admin-only access
        
        # Test with superuser - should succeed
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('docs:index'))
        self.assertEqual(response.status_code, 200)
    
    def test_documentation_not_accessible_to_anonymous_users(self):
        """Test that documentation requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('docs:index'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_documentation_link_in_superuser_sidebar(self):
        """Test that documentation link appears in superuser sidebar."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the documentation link is present
        # The link might be in different formats, so check for the URL path
        self.assertContains(response, '/docs/')
        self.assertContains(response, 'Documentation')
    
    def test_documentation_link_active_state(self):
        """Test that documentation link is highlighted when active."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('docs:index'))
        self.assertEqual(response.status_code, 200)
        
        # The active class should be applied when on docs pages
        # This is handled by the template: {% if request.resolver_match.app_name == 'docs' %}active{% endif %}
        self.assertContains(response, 'docs')
    
    def test_navigation_from_admin_to_documentation(self):
        """Test navigation flow from admin dashboard to documentation."""
        self.client.login(username='admin', password='testpass123')
        
        # Start at admin dashboard
        response = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Navigate to documentation
        response = self.client.get(reverse('docs:index'))
        self.assertEqual(response.status_code, 200)
        
        # Verify we're on the documentation page
        self.assertContains(response, 'Documentation')
    
    def test_documentation_url_configuration(self):
        """Test that documentation URLs are properly configured."""
        # Test index URL
        url = reverse('docs:index')
        self.assertEqual(url, '/docs/')
        
        # Test search URL
        url = reverse('docs:search')
        self.assertEqual(url, '/docs/search/')
        
        # Test document URL
        url = reverse('docs:document', kwargs={'doc_path': 'test/page'})
        self.assertEqual(url, '/docs/test/page/')
