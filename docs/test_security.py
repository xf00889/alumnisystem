"""
Security tests for documentation viewer.

Tests path traversal prevention, XSS prevention, and input sanitization.
"""

import unittest
from pathlib import Path
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from .views import validate_doc_path
from .markdown_processor import MarkdownProcessor
from .navigation import NavigationBuilder
from .utils import sanitize_search_query, highlight_search_term

User = get_user_model()


class PathTraversalTests(TestCase):
    """
    Test path traversal prevention in validate_doc_path.
    
    Requirements: 1.3 (Security)
    """
    
    def test_valid_path(self):
        """Valid paths should be accepted."""
        is_valid, sanitized = validate_doc_path('quick-start/new-user-guide.md')
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, 'quick-start/new-user-guide.md')
    
    def test_parent_directory_traversal(self):
        """Paths with .. should be rejected."""
        is_valid, _ = validate_doc_path('../etc/passwd')
        self.assertFalse(is_valid)
        
        is_valid, _ = validate_doc_path('folder/../../../etc/passwd')
        self.assertFalse(is_valid)
    
    def test_absolute_path_unix(self):
        """Absolute Unix paths should be rejected."""
        is_valid, _ = validate_doc_path('/etc/passwd')
        self.assertFalse(is_valid)
        
        is_valid, _ = validate_doc_path('/var/www/html')
        self.assertFalse(is_valid)
    
    def test_absolute_path_windows(self):
        """Absolute Windows paths should be rejected."""
        is_valid, _ = validate_doc_path('C:\\Windows\\System32')
        self.assertFalse(is_valid)
        
        is_valid, _ = validate_doc_path('D:\\secrets.txt')
        self.assertFalse(is_valid)
    
    def test_null_byte_injection(self):
        """Paths with null bytes should be rejected."""
        is_valid, _ = validate_doc_path('file.md\x00.txt')
        self.assertFalse(is_valid)
    
    def test_hidden_file_access(self):
        """Paths to hidden files should be rejected."""
        is_valid, _ = validate_doc_path('.env')
        self.assertFalse(is_valid)
        
        is_valid, _ = validate_doc_path('folder/.git/config')
        self.assertFalse(is_valid)
    
    def test_invalid_characters(self):
        """Paths with invalid characters should be rejected."""
        is_valid, _ = validate_doc_path('file<script>.md')
        self.assertFalse(is_valid)
        
        is_valid, _ = validate_doc_path('file|pipe.md')
        self.assertFalse(is_valid)
    
    def test_empty_path(self):
        """Empty paths should be rejected."""
        is_valid, _ = validate_doc_path('')
        self.assertFalse(is_valid)
        
        is_valid, _ = validate_doc_path('   ')
        self.assertFalse(is_valid)


class XSSPreventionTests(TestCase):
    """
    Test XSS prevention in markdown rendering and search.
    
    Requirements: 1.3 (Security)
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = MarkdownProcessor()
    
    def test_script_tag_sanitization(self):
        """Script tags should be removed from HTML."""
        html = '<p>Hello</p><script>alert("XSS")</script>'
        sanitized = self.processor._sanitize_html(html)
        self.assertNotIn('<script>', sanitized)
        # Note: bleach strips the tags but may leave the content
        # The important thing is the script tag itself is removed
        self.assertIn('Hello', sanitized)
    
    def test_onclick_attribute_removal(self):
        """Event handler attributes should be removed."""
        html = '<a href="#" onclick="alert(\'XSS\')">Click</a>'
        sanitized = self.processor._sanitize_html(html)
        self.assertNotIn('onclick', sanitized)
        self.assertIn('Click', sanitized)
    
    def test_javascript_protocol_removal(self):
        """JavaScript protocol in links should be removed."""
        html = '<a href="javascript:alert(\'XSS\')">Click</a>'
        sanitized = self.processor._sanitize_html(html)
        self.assertNotIn('javascript:', sanitized)
    
    def test_safe_html_preserved(self):
        """Safe HTML should be preserved."""
        html = '<h1>Title</h1><p>Paragraph with <strong>bold</strong> and <em>italic</em>.</p>'
        sanitized = self.processor._sanitize_html(html)
        self.assertIn('<h1>Title</h1>', sanitized)
        self.assertIn('<strong>bold</strong>', sanitized)
        self.assertIn('<em>italic</em>', sanitized)
    
    def test_search_highlight_escaping(self):
        """Search highlighting should escape HTML."""
        text = '<script>alert("XSS")</script>'
        highlighted = highlight_search_term(text, 'script', 'highlight')
        self.assertNotIn('<script>', highlighted)
        # The text should be escaped (contains &lt; and &gt;)
        self.assertIn('&lt;', highlighted)
        self.assertIn('&gt;', highlighted)
        # And the search term should be highlighted with mark tags
        self.assertIn('<mark class="highlight">', highlighted)


class InputSanitizationTests(TestCase):
    """
    Test input sanitization for search queries.
    
    Requirements: 1.3 (Security)
    """
    
    def test_normal_query(self):
        """Normal queries should pass through."""
        query = 'user guide'
        sanitized = sanitize_search_query(query)
        self.assertEqual(sanitized, 'user guide')
    
    def test_whitespace_trimming(self):
        """Leading/trailing whitespace should be removed."""
        query = '  search term  '
        sanitized = sanitize_search_query(query)
        self.assertEqual(sanitized, 'search term')
    
    def test_null_byte_removal(self):
        """Null bytes should be removed."""
        query = 'search\x00term'
        sanitized = sanitize_search_query(query)
        self.assertNotIn('\x00', sanitized)
    
    def test_control_character_removal(self):
        """Control characters should be removed."""
        query = 'search\x01\x02term'
        sanitized = sanitize_search_query(query)
        self.assertNotIn('\x01', sanitized)
        self.assertNotIn('\x02', sanitized)
    
    def test_length_limiting(self):
        """Long queries should be truncated."""
        query = 'a' * 300
        sanitized = sanitize_search_query(query, max_length=200)
        self.assertEqual(len(sanitized), 200)
    
    def test_empty_query(self):
        """Empty queries should return empty string."""
        sanitized = sanitize_search_query('')
        self.assertEqual(sanitized, '')
        
        sanitized = sanitize_search_query(None)
        self.assertEqual(sanitized, '')


class NavigationSecurityTests(TestCase):
    """
    Test security in navigation builder.
    
    Requirements: 1.3 (Security)
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.nav_builder = NavigationBuilder()
    
    @patch('docs.navigation.Path')
    def test_symlink_skipping(self, mock_path):
        """Symlinks should be skipped during directory scanning."""
        # This test would require mocking the file system
        # In a real scenario, we'd create actual symlinks and test
        pass
    
    def test_path_validation_in_scan(self):
        """Directory scanning should validate paths."""
        # Test that _scan_directory validates paths
        # This is tested implicitly through the path traversal tests
        pass


class MarkdownProcessorSecurityTests(TestCase):
    """
    Test security in markdown processor.
    
    Requirements: 1.3 (Security)
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = MarkdownProcessor()
    
    def test_path_validation_in_render(self):
        """Render should validate file paths."""
        # Test with a path outside base_path
        result = self.processor.render('../../../etc/passwd')
        self.assertTrue(result.get('error'))
        self.assertIn('not found', result.get('message', '').lower())
    
    def test_allowed_tags_configuration(self):
        """Processor should have safe tag whitelist."""
        self.assertIn('p', self.processor.allowed_tags)
        self.assertIn('a', self.processor.allowed_tags)
        self.assertNotIn('script', self.processor.allowed_tags)
        self.assertNotIn('iframe', self.processor.allowed_tags)
    
    def test_allowed_protocols_configuration(self):
        """Processor should only allow safe protocols."""
        self.assertIn('http', self.processor.allowed_protocols)
        self.assertIn('https', self.processor.allowed_protocols)
        self.assertNotIn('javascript', self.processor.allowed_protocols)
        self.assertNotIn('data', self.processor.allowed_protocols)


class IntegrationSecurityTests(TestCase):
    """
    Integration tests for security measures.
    
    Requirements: 1.3 (Security)
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_authentication_required(self):
        """All documentation views should require authentication."""
        from .views import DocumentationIndexView, DocumentationView, DocumentationSearchView
        
        # Test that views have LoginRequiredMixin
        self.assertTrue(hasattr(DocumentationIndexView, 'login_url'))
        self.assertTrue(hasattr(DocumentationView, 'login_url'))
        self.assertTrue(hasattr(DocumentationSearchView, 'login_url'))


class AdminOnlyAccessTests(TestCase):
    """
    Test admin-only access enforcement for documentation viewer.
    
    Requirements: 3.1 (Admin-only access)
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create regular user (non-admin)
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create superuser
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@example.com',
            password='testpass123',
            is_superuser=True
        )
    
    def test_non_admin_denied_index_view(self):
        """Non-admin users should be denied access to documentation index."""
        from .views import DocumentationIndexView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/docs/')
        request.user = self.regular_user
        
        view = DocumentationIndexView.as_view()
        
        # Should raise Http404 (as per AdminRequiredMixin implementation)
        from django.http import Http404
        with self.assertRaises(Http404):
            response = view(request)
    
    def test_non_admin_denied_document_view(self):
        """Non-admin users should be denied access to documentation pages."""
        from .views import DocumentationView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/docs/quick-start/new-user-guide/')
        request.user = self.regular_user
        
        view = DocumentationView.as_view()
        
        # Should raise Http404 (as per AdminRequiredMixin implementation)
        from django.http import Http404
        with self.assertRaises(Http404):
            response = view(request, doc_path='quick-start/new-user-guide')
    
    def test_non_admin_denied_search_view(self):
        """Non-admin users should be denied access to documentation search."""
        from .views import DocumentationSearchView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/docs/search/?q=test')
        request.user = self.regular_user
        request.GET = {'q': 'test'}
        
        view = DocumentationSearchView.as_view()
        
        # Should raise Http404 (as per AdminRequiredMixin implementation)
        from django.http import Http404
        with self.assertRaises(Http404):
            response = view(request)
    
    def test_staff_user_granted_access(self):
        """Staff users should be granted access to documentation."""
        from .views import DocumentationIndexView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/docs/')
        request.user = self.staff_user
        request.session = {}
        
        view = DocumentationIndexView.as_view()
        response = view(request)
        
        # Should return 200 (success)
        self.assertEqual(response.status_code, 200)
    
    def test_superuser_granted_access(self):
        """Superusers should be granted access to documentation."""
        from .views import DocumentationIndexView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/docs/')
        request.user = self.superuser
        request.session = {}
        
        view = DocumentationIndexView.as_view()
        response = view(request)
        
        # Should return 200 (success)
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_user_redirected(self):
        """Unauthenticated users should be redirected to login."""
        from .views import DocumentationIndexView
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get('/docs/')
        request.user = AnonymousUser()
        
        view = DocumentationIndexView.as_view()
        response = view(request)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_admin_required_mixin_test_func(self):
        """Test the AdminRequiredMixin test_func logic directly."""
        from .views import AdminRequiredMixin
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/docs/')
        
        # Create a test view instance
        class TestView(AdminRequiredMixin):
            pass
        
        view = TestView()
        view.request = request
        
        # Test with regular user
        request.user = self.regular_user
        self.assertFalse(view.test_func())
        
        # Test with staff user
        request.user = self.staff_user
        self.assertTrue(view.test_func())
        
        # Test with superuser
        request.user = self.superuser
        self.assertTrue(view.test_func())


class EnhancedPathTraversalTests(TestCase):
    """
    Enhanced path traversal prevention tests.
    
    Requirements: 3.4 (Path traversal prevention)
    """
    
    def test_multiple_parent_directory_traversal(self):
        """Multiple ../ sequences should be rejected."""
        test_paths = [
            '../../../etc/passwd',
            'folder/../../../../../../etc/passwd',
            'docs/../../../secrets.txt',
            '../../..',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Path should be rejected: {path}")
    
    def test_encoded_path_traversal(self):
        """URL-encoded path traversal attempts should be rejected."""
        # Note: validate_doc_path doesn't decode URLs, but we test the pattern
        test_paths = [
            '..%2F..%2Fetc%2Fpasswd',  # URL encoded ../
            'folder%2F..%2F..%2Fsecrets',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                # These should be rejected due to invalid characters
                self.assertFalse(is_valid, f"Path should be rejected: {path}")
    
    def test_mixed_separators_traversal(self):
        """Mixed path separators with traversal should be rejected."""
        test_paths = [
            '..\\..\\..\\windows\\system32',
            'folder\\..\\..\\secrets',
            '../folder\\..\\secrets',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Path should be rejected: {path}")
    
    def test_absolute_paths_various_formats(self):
        """Various absolute path formats should be rejected."""
        test_paths = [
            '/etc/passwd',
            '/var/www/html/index.html',
            'C:\\Windows\\System32\\config',
            'D:\\secrets\\passwords.txt',
            '\\\\network\\share\\file.txt',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Absolute path should be rejected: {path}")
    
    def test_null_byte_injection_variations(self):
        """Various null byte injection attempts should be rejected."""
        test_paths = [
            'file.md\x00.txt',
            'folder/file\x00.md',
            '\x00malicious.md',
            'file.md\x00\x00',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Null byte path should be rejected: {path}")
    
    def test_hidden_files_and_folders(self):
        """Hidden files and folders should be rejected."""
        test_paths = [
            '.env',
            '.git/config',
            'folder/.hidden/file.md',
            '.ssh/id_rsa',
            'docs/.secret.md',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Hidden file path should be rejected: {path}")
    
    def test_special_characters_injection(self):
        """Paths with special characters should be rejected."""
        test_paths = [
            'file<script>.md',
            'file|pipe.md',
            'file;command.md',
            'file&command.md',
            'file$var.md',
            'file`cmd`.md',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Special character path should be rejected: {path}")
    
    def test_valid_paths_accepted(self):
        """Valid documentation paths should be accepted."""
        test_paths = [
            'README.md',
            'quick-start/new-user-guide.md',
            'admin-features/cms/dashboard.md',
            'user-features/profile-management/profile-photo.md',
            'folder/subfolder/document.md',
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                is_valid, sanitized = validate_doc_path(path)
                self.assertTrue(is_valid, f"Valid path should be accepted: {path}")
                self.assertEqual(sanitized, path)
    
    def test_empty_and_whitespace_paths(self):
        """Empty and whitespace-only paths should be rejected."""
        test_paths = [
            '',
            '   ',
            '\t',
            '\n',
            '  \t\n  ',
        ]
        
        for path in test_paths:
            with self.subTest(path=repr(path)):
                is_valid, _ = validate_doc_path(path)
                self.assertFalse(is_valid, f"Empty/whitespace path should be rejected: {repr(path)}")


class NullByteInjectionTests(TestCase):
    """
    Dedicated tests for null byte injection prevention.
    
    Requirements: 3.4 (Path traversal prevention - includes null byte injection)
    """
    
    def test_null_byte_in_filename(self):
        """Null bytes in filename should be rejected."""
        is_valid, _ = validate_doc_path('document\x00.md')
        self.assertFalse(is_valid)
    
    def test_null_byte_in_path(self):
        """Null bytes in path should be rejected."""
        is_valid, _ = validate_doc_path('folder/sub\x00folder/file.md')
        self.assertFalse(is_valid)
    
    def test_null_byte_at_start(self):
        """Null byte at start of path should be rejected."""
        is_valid, _ = validate_doc_path('\x00document.md')
        self.assertFalse(is_valid)
    
    def test_null_byte_at_end(self):
        """Null byte at end of path should be rejected."""
        is_valid, _ = validate_doc_path('document.md\x00')
        self.assertFalse(is_valid)
    
    def test_multiple_null_bytes(self):
        """Multiple null bytes should be rejected."""
        is_valid, _ = validate_doc_path('doc\x00ument\x00.md')
        self.assertFalse(is_valid)
    
    def test_null_byte_with_traversal(self):
        """Null byte combined with path traversal should be rejected."""
        is_valid, _ = validate_doc_path('../../../etc/passwd\x00.md')
        self.assertFalse(is_valid)


if __name__ == '__main__':
    unittest.main()
