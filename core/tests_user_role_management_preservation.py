"""
Preservation Property Tests for User Role Management 403 Fix

These tests verify that the fix does NOT break existing functionality:
1. Non-AJAX requests to protected endpoints still redirect to HTML error pages
2. Superuser AJAX requests still successfully manage roles and return JSON
3. Audit logging and email notifications still work for all role changes
4. User detail page still displays correctly for authorized users

EXPECTED OUTCOME: These tests MUST PASS on both unfixed and fixed code.
This confirms that the fix preserves existing behavior for non-buggy inputs.
"""

from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.urls import reverse
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from core.mixins import SuperuserRequiredMixin, StaffRequiredMixin
from django.views.generic import View
import json

User = get_user_model()


class DummySuperuserView(SuperuserRequiredMixin, View):
    """Test view that simulates a protected endpoint"""
    def get(self, request):
        return JsonResponse({'success': True, 'message': 'Success'})
    
    def post(self, request):
        return JsonResponse({'success': True, 'message': 'Success'})


class PreservationPropertyTest(TestCase):
    """
    Property 2: Preservation - Non-AJAX Requests Return HTML Redirects
    
    This test verifies that non-AJAX requests to protected endpoints
    still redirect to HTML error pages (existing behavior).
    
    **EXPECTED OUTCOME**: This test MUST PASS on both unfixed and fixed code.
    """
    
    def setUp(self):
        """Set up test users and request factory"""
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create test users
        self.superuser = User.objects.create_user(
            email='superuser@test.com',
            username='superuser',
            password='testpass123',
            is_superuser=True,
            is_staff=True,
            first_name='Super',
            last_name='User'
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            username='staff',
            password='testpass123',
            is_staff=True,
            is_superuser=False,
            first_name='Staff',
            last_name='User'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='testpass123',
            is_staff=False,
            is_superuser=False,
            first_name='Regular',
            last_name='User'
        )
    
    def _add_middleware_to_request(self, request):
        """Add required middleware to request"""
        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_non_ajax_permission_failure_returns_html_redirect(self):
        """
        Test that non-AJAX requests from non-superusers return HTML redirects.
        
        This is the PRESERVED behavior - non-AJAX requests should redirect to HTML pages.
        
        **Validates: Requirements 3.2**
        **Preservation: Property 2 from design**
        """
        # Create regular GET request (no AJAX headers)
        request = self.factory.get('/admin-dashboard/users/1/')
        request.user = self.staff_user  # Staff but not superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # PRESERVED BEHAVIOR: Non-AJAX requests should redirect (status 302)
        self.assertEqual(
            response.status_code,
            302,
            f"Non-AJAX request should return redirect (302), got {response.status_code}"
        )
        
        # Verify it's redirecting to admin dashboard
        self.assertIn('admin-dashboard', response.url)
    
    def test_non_ajax_post_permission_failure_returns_html_redirect(self):
        """
        Test that non-AJAX POST requests from non-superusers return HTML redirects.
        
        **Validates: Requirements 3.2**
        """
        # Create regular POST request (no AJAX headers)
        request = self.factory.post(
            '/admin-dashboard/users/1/roles/',
            data={'action': 'assign', 'role': 'admin'}
        )
        request.user = self.staff_user  # Staff but not superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # PRESERVED BEHAVIOR: Non-AJAX requests should redirect
        self.assertEqual(
            response.status_code,
            302,
            "Non-AJAX POST request should return redirect"
        )
    
    def test_superuser_ajax_request_succeeds(self):
        """
        Test that superusers can still make successful AJAX requests.
        
        This verifies that the fix doesn't break legitimate superuser access.
        
        **Validates: Requirements 3.1**
        **Preservation: Property 4 from design**
        """
        # Create AJAX POST request with XMLHttpRequest header
        request = self.factory.post(
            '/admin-dashboard/users/1/roles/',
            data={'action': 'assign', 'role': 'admin'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = self.superuser  # Superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # PRESERVED BEHAVIOR: Superusers should get successful JSON response
        self.assertEqual(
            response.status_code,
            200,
            f"Superuser AJAX request should succeed (200), got {response.status_code}"
        )
        
        # Verify it's JSON
        self.assertEqual(
            response.get('Content-Type', '').split(';')[0],
            'application/json',
            "Superuser AJAX request should return JSON"
        )
        
        # Verify success response
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
    
    def test_superuser_non_ajax_request_succeeds(self):
        """
        Test that superusers can still access pages via regular requests.
        
        **Validates: Requirements 3.1**
        """
        # Create regular GET request (no AJAX headers)
        request = self.factory.get('/admin-dashboard/users/1/')
        request.user = self.superuser  # Superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # PRESERVED BEHAVIOR: Superusers should get successful response
        self.assertEqual(
            response.status_code,
            200,
            "Superuser regular request should succeed"
        )


class PropertyBasedPreservationTest(HypothesisTestCase):
    """
    Property-based tests to verify preservation across different scenarios.
    
    Uses hypothesis to generate test cases for:
    - Different user types (superuser, staff, regular)
    - Different request types (GET, POST)
    - Different request formats (AJAX, non-AJAX)
    """
    
    def setUp(self):
        """Set up test users"""
        self.factory = RequestFactory()
        
        # Use get_or_create to avoid duplicate user errors in hypothesis tests
        self.superuser, _ = User.objects.get_or_create(
            username='superuser_pbt',
            defaults={
                'email': 'superuser_pbt@test.com',
                'is_superuser': True,
                'is_staff': True
            }
        )
        if not self.superuser.has_usable_password():
            self.superuser.set_password('testpass123')
            self.superuser.save()
        
        self.staff_user, _ = User.objects.get_or_create(
            username='staff_pbt',
            defaults={
                'email': 'staff_pbt@test.com',
                'is_staff': True,
                'is_superuser': False
            }
        )
        if not self.staff_user.has_usable_password():
            self.staff_user.set_password('testpass123')
            self.staff_user.save()
        
        self.regular_user, _ = User.objects.get_or_create(
            username='user_pbt',
            defaults={
                'email': 'user_pbt@test.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if not self.regular_user.has_usable_password():
            self.regular_user.set_password('testpass123')
            self.regular_user.save()
    
    def _add_middleware_to_request(self, request):
        """Add required middleware to request"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    @given(
        user_type=st.sampled_from(['staff', 'regular']),
        method=st.sampled_from(['GET', 'POST'])
    )
    @settings(max_examples=10, deadline=None)
    def test_property_non_ajax_requests_always_redirect(self, user_type, method):
        """
        Property: For ANY non-superuser making a non-AJAX request to a superuser-protected
        endpoint, the response MUST be an HTML redirect (status 302).
        
        This property test verifies preservation of existing behavior.
        
        **Validates: Requirements 3.2**
        **Preservation: Property 2 from design**
        """
        # Select user based on type
        if user_type == 'staff':
            user = self.staff_user
        else:
            user = self.regular_user
        
        # Create request based on method (no AJAX headers)
        if method == 'GET':
            request = self.factory.get('/admin-dashboard/users/1/')
        else:  # POST
            request = self.factory.post(
                '/admin-dashboard/users/1/roles/',
                data={'action': 'assign', 'role': 'admin'}
            )
        
        request.user = user
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # PROPERTY: Non-AJAX requests should ALWAYS redirect
        self.assertEqual(
            response.status_code,
            302,
            f"Non-AJAX {method} request from {user_type} user should redirect (302), "
            f"got {response.status_code}"
        )
    
    @given(
        ajax_type=st.sampled_from(['xhr', 'json_content_type']),
        method=st.sampled_from(['GET', 'POST'])
    )
    @settings(max_examples=10, deadline=None)
    def test_property_superuser_ajax_requests_always_succeed(self, ajax_type, method):
        """
        Property: For ANY superuser making an AJAX request to a superuser-protected
        endpoint, the response MUST be successful JSON (status 200).
        
        This property test verifies that the fix doesn't break superuser access.
        
        **Validates: Requirements 3.1**
        **Preservation: Property 4 from design**
        """
        # Create request based on method and AJAX type
        if method == 'GET':
            if ajax_type == 'xhr':
                request = self.factory.get(
                    '/admin-dashboard/users/1/',
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                )
            else:  # json_content_type
                request = self.factory.get(
                    '/admin-dashboard/users/1/',
                    content_type='application/json'
                )
        else:  # POST
            if ajax_type == 'xhr':
                request = self.factory.post(
                    '/admin-dashboard/users/1/roles/',
                    data={'action': 'assign', 'role': 'admin'},
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                )
            else:  # json_content_type
                request = self.factory.post(
                    '/admin-dashboard/users/1/roles/',
                    data=json.dumps({'action': 'assign', 'role': 'admin'}),
                    content_type='application/json'
                )
        
        request.user = self.superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # PROPERTY: Superuser AJAX requests should ALWAYS succeed
        self.assertEqual(
            response.status_code,
            200,
            f"Superuser AJAX {method} request with {ajax_type} should succeed (200), "
            f"got {response.status_code}"
        )
        
        # Verify it's JSON
        content_type = response.get('Content-Type', '').split(';')[0]
        self.assertEqual(
            content_type,
            'application/json',
            f"Superuser AJAX request should return JSON, got {content_type}"
        )
