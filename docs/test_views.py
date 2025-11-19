"""
Tests for documentation viewer views.

Tests the DocumentationIndexView, DocumentationView, and DocumentationSearchView
to ensure they properly integrate with markdown processing and navigation.
"""
from django.test import TestCase, RequestFactory, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.urls import reverse
from pathlib import Path
import tempfile
import shutil

from .views import DocumentationIndexView, DocumentationView, DocumentationSearchView, validate_doc_path
from .markdown_processor import MarkdownProcessor
from .navigation import NavigationBuilder


User = get_user_model()


class DocumentationIndexViewTest(TestCase):
    """
    Test the main documentation landing page view.
    
    Requirements: 1.2, 1.3, 1.4
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.view = DocumentationIndexView.as_view()
    
    def test_requires_authentication(self):
        """Test that the view requires authentication."""
        request = self.factory.get('/docs/')
        request.user = AnonymousUser()
        
        # The view should redirect to login (handled by LoginRequiredMixin)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
    
    def test_authenticated_user_can_access(self):
        """Test that admin users can access the index."""
        # Make user an admin
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        request = self.factory.get('/docs/')
        request.user = self.user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_context_contains_required_data(self):
        """Test that context includes TOC and README content."""
        # Make user an admin
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        request = self.factory.get('/docs/')
        request.user = self.user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        context = response.context_data
        
        # Check required context keys
        self.assertIn('toc', context)
        self.assertIn('current_path', context)
        self.assertIn('is_index', context)
        self.assertEqual(context['current_path'], '')
        self.assertTrue(context['is_index'])


class DocumentationViewTest(TestCase):
    """
    Test individual documentation page view.
    
    Requirements: 1.2, 1.3, 1.4, 4.3, 4.4, 4.5, 7.1, 7.2, 7.3, 7.4
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.view = DocumentationView.as_view()
    
    def test_requires_authentication(self):
        """Test that the view requires authentication."""
        request = self.factory.get('/docs/test/')
        request.user = AnonymousUser()
        
        response = self.view(request, doc_path='test')
        self.assertEqual(response.status_code, 302)
    
    def test_authenticated_user_can_access(self):
        """Test that admin users can access documents."""
        # Make user an admin
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        request = self.factory.get('/docs/README/')
        request.user = self.user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request, doc_path='README')
        self.assertEqual(response.status_code, 200)
    
    def test_context_contains_navigation_data(self):
        """Test that context includes TOC, breadcrumbs, and prev/next."""
        # Make user an admin
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        request = self.factory.get('/docs/README/')
        request.user = self.user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request, doc_path='README')
        context = response.context_data
        
        # Check required context keys
        self.assertIn('toc', context)
        self.assertIn('breadcrumbs', context)
        self.assertIn('prev_doc', context)
        self.assertIn('next_doc', context)
        self.assertIn('current_path', context)
        self.assertIn('is_index', context)
        self.assertFalse(context['is_index'])
    
    def test_missing_document_returns_404(self):
        """Test that missing documents return 404 status with error page."""
        # Make user an admin
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        request = self.factory.get('/docs/nonexistent/')
        request.user = self.user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request, doc_path='nonexistent')
        
        # Should return 404 status code
        self.assertEqual(response.status_code, 404)
        
        # Response should contain 404 error page content
        content = response.content.decode('utf-8')
        self.assertIn('404', content)
        self.assertIn('Document Not Found', content)
    
    def test_adds_md_extension_if_missing(self):
        """Test that .md extension is added if not present."""
        # Make user an admin
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        request = self.factory.get('/docs/README/')
        request.user = self.user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request, doc_path='README')
        context = response.context_data
        
        # The doc_path should have .md added
        self.assertTrue(context['current_path'].endswith('.md'))


class DocumentationSearchViewTest(TestCase):
    """
    Test documentation search view.
    
    Requirements: 3.5, 4.7, 7.5
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        self.view = DocumentationSearchView.as_view()
    
    def test_requires_authentication(self):
        """Test that the view requires authentication."""
        request = self.factory.get('/docs/search/')
        request.user = AnonymousUser()
        
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
    
    def test_authenticated_user_can_access(self):
        """Test that authenticated non-admin users cannot access search."""
        request = self.factory.get('/docs/search/')
        request.user = self.user
        
        # Non-admin users should be denied access
        # AdminRequiredMixin raises Http404 for non-admin authenticated users
        with self.assertRaises(Http404):
            self.view(request)
    
    def test_context_contains_query_and_results(self):
        """Test that context includes query and results."""
        request = self.factory.get('/docs/search/?q=test')
        request.user = self.admin_user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        context = response.context_data
        
        # Check required context keys
        self.assertIn('toc', context)
        self.assertIn('query', context)
        self.assertIn('results', context)
        self.assertIn('is_search', context)
        self.assertEqual(context['query'], 'test')
        self.assertTrue(context['is_search'])
    
    def test_empty_query_shows_message(self):
        """Test that empty query shows appropriate message."""
        request = self.factory.get('/docs/search/')
        request.user = self.admin_user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        context = response.context_data
        
        self.assertEqual(context['query'], '')
        self.assertIn('message', context)
    
    def test_search_returns_only_permitted_documents(self):
        """
        Test that search returns only documents the user has permission to view.
        Requirements: 3.5
        
        Since all documentation requires admin access, non-admin users should
        not be able to access search results.
        """
        # Non-admin user should be denied access (handled by AdminRequiredMixin)
        request = self.factory.get('/docs/search/?q=test')
        request.user = self.user
        
        # The view should deny access to non-admin users
        # AdminRequiredMixin will raise Http404 for non-admin authenticated users
        with self.assertRaises(Http404):
            self.view(request)
    
    def test_admin_user_can_search(self):
        """
        Test that admin users can perform searches.
        Requirements: 3.5
        """
        request = self.factory.get('/docs/search/?q=test')
        request.user = self.admin_user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should have search results context
        context = response.context_data
        self.assertIn('results', context)
        self.assertIn('query', context)
    
    def test_search_with_special_characters(self):
        """
        Test that search handles special characters safely.
        Requirements: 7.5
        """
        request = self.factory.get('/docs/search/?q=test\x00\x01query')
        request.user = self.admin_user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        
        # Query should be sanitized - control characters should be removed
        context = response.context_data
        self.assertNotIn('\x00', context['query'])
        self.assertNotIn('\x01', context['query'])
    
    def test_search_with_long_query(self):
        """
        Test that search handles very long queries.
        Requirements: 7.5
        """
        long_query = 'a' * 300
        request = self.factory.get(f'/docs/search/?q={long_query}')
        request.user = self.admin_user
        # Add session support
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        
        # Query should be truncated
        context = response.context_data
        self.assertLessEqual(len(context['query']), 200)


class URLValidationTest(TestCase):
    """
    Test URL path validation and sanitization.
    
    Requirements: 4.3, 4.4
    """
    
    def test_valid_simple_path(self):
        """Test that simple valid paths are accepted."""
        is_valid, sanitized = validate_doc_path('README.md')
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, 'README.md')
    
    def test_valid_nested_path(self):
        """Test that nested valid paths are accepted."""
        is_valid, sanitized = validate_doc_path('admin-features/cms/dashboard.md')
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, 'admin-features/cms/dashboard.md')
    
    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        is_valid, sanitized = validate_doc_path('../../../etc/passwd')
        self.assertFalse(is_valid)
        
        is_valid, sanitized = validate_doc_path('docs/../../secrets.txt')
        self.assertFalse(is_valid)
    
    def test_absolute_path_rejected(self):
        """Test that absolute paths are rejected."""
        is_valid, sanitized = validate_doc_path('/etc/passwd')
        self.assertFalse(is_valid)
    
    def test_hidden_files_rejected(self):
        """Test that hidden files/folders are rejected."""
        is_valid, sanitized = validate_doc_path('.hidden/file.md')
        self.assertFalse(is_valid)
        
        is_valid, sanitized = validate_doc_path('docs/.secret.md')
        self.assertFalse(is_valid)
    
    def test_null_bytes_removed(self):
        """Test that null bytes are removed."""
        is_valid, sanitized = validate_doc_path('test\x00file.md')
        # Should be rejected due to null byte removal changing the path
        self.assertFalse(is_valid)
    
    def test_invalid_characters_rejected(self):
        """Test that invalid characters are rejected."""
        is_valid, sanitized = validate_doc_path('test<script>.md')
        self.assertFalse(is_valid)
        
        is_valid, sanitized = validate_doc_path('test;rm -rf.md')
        self.assertFalse(is_valid)
    
    def test_empty_path_rejected(self):
        """Test that empty paths are rejected."""
        is_valid, sanitized = validate_doc_path('')
        self.assertFalse(is_valid)
        
        is_valid, sanitized = validate_doc_path('   ')
        self.assertFalse(is_valid)
    
    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from paths."""
        is_valid, sanitized = validate_doc_path('  README.md  ')
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, 'README.md')
    
    def test_slashes_stripped(self):
        """Test that trailing slashes are stripped but leading slashes are rejected."""
        # Leading slash should be rejected (absolute path)
        is_valid, sanitized = validate_doc_path('/README.md')
        self.assertFalse(is_valid)
        
        # Trailing slash should be stripped
        is_valid, sanitized = validate_doc_path('README.md/')
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, 'README.md')


@override_settings(
    # Disable setup middleware for tests
    MIDDLEWARE=[m for m in __import__('django.conf', fromlist=['settings']).settings.MIDDLEWARE 
                if 'SetupRequiredMiddleware' not in m]
)
class SessionStorageTest(TestCase):
    """
    Test session storage for last-viewed page.
    
    Requirements: 4.6
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        # Enable session
        session = self.client.session
        session.save()
        self.client.login(username='testuser', password='testpass123')
    
    def test_index_view_stores_last_viewed(self):
        """Test that index view stores last viewed page in session."""
        response = self.client.get(reverse('docs:index'))
        self.assertEqual(response.status_code, 200)
        
        # Check session contains last viewed page
        session = self.client.session
        self.assertIn('docs_last_viewed', session)
        self.assertEqual(session['docs_last_viewed'], '/docs/')
    
    def test_document_view_stores_last_viewed(self):
        """Test that document view stores last viewed page in session."""
        response = self.client.get(reverse('docs:document', kwargs={'doc_path': 'README'}))
        
        # Check session contains last viewed page
        session = self.client.session
        self.assertIn('docs_last_viewed', session)
        self.assertIn('README', session['docs_last_viewed'])
    
    def test_search_view_stores_last_viewed(self):
        """Test that search view stores last viewed page with query in session."""
        response = self.client.get(reverse('docs:search') + '?q=test')
        self.assertEqual(response.status_code, 200)
        
        # Check session contains last viewed page with query
        session = self.client.session
        self.assertIn('docs_last_viewed', session)
        self.assertIn('search', session['docs_last_viewed'])
        self.assertIn('q=test', session['docs_last_viewed'])
    
    def test_last_viewed_updates_on_navigation(self):
        """Test that last viewed page updates as user navigates."""
        # Visit index
        self.client.get(reverse('docs:index'))
        session = self.client.session
        first_page = session['docs_last_viewed']
        
        # Visit a document
        self.client.get(reverse('docs:document', kwargs={'doc_path': 'README'}))
        session = self.client.session
        second_page = session['docs_last_viewed']
        
        # Pages should be different
        self.assertNotEqual(first_page, second_page)
        self.assertIn('README', second_page)
    
    def test_last_viewed_available_in_context(self):
        """Test that last viewed page is available in template context."""
        # Visit a document first
        self.client.get(reverse('docs:document', kwargs={'doc_path': 'README'}))
        
        # Visit index
        response = self.client.get(reverse('docs:index'))
        
        # Check context contains last viewed page
        self.assertIn('last_viewed_page', response.context)
        self.assertIn('README', response.context['last_viewed_page'])


@override_settings(
    # Disable setup middleware for tests
    MIDDLEWARE=[m for m in __import__('django.conf', fromlist=['settings']).settings.MIDDLEWARE 
                if 'SetupRequiredMiddleware' not in m]
)
class BrowserNavigationTest(TestCase):
    """
    Test browser back/forward navigation support.
    
    Requirements: 4.5
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        # Enable session
        session = self.client.session
        session.save()
        self.client.login(username='testuser', password='testpass123')
    
    def test_url_updates_on_navigation(self):
        """Test that URL properly updates when navigating between pages."""
        # Visit index
        response = self.client.get(reverse('docs:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/docs/')
        
        # Visit a document
        response = self.client.get(reverse('docs:document', kwargs={'doc_path': 'README'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('README', response.request['PATH_INFO'])
    
    def test_direct_url_access_works(self):
        """Test that direct URL access to documents works."""
        # Directly access a nested document
        response = self.client.get('/docs/quick-start/new-user-guide/')
        
        # Should work (or 404 if file doesn't exist, but not 500)
        self.assertIn(response.status_code, [200, 404])
    
    def test_url_with_query_params_works(self):
        """Test that URLs with query parameters work correctly."""
        response = self.client.get(reverse('docs:search') + '?q=test&page=1')
        self.assertEqual(response.status_code, 200)
        
        # Query should be in context
        self.assertEqual(response.context['query'], 'test')
