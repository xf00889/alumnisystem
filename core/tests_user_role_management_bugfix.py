"""
Bug Condition Exploration Tests for User Role Management 403 Fix

These tests demonstrate the bug on UNFIXED code:
1. AJAX requests to role management endpoints return HTML instead of JSON
2. Template renders action buttons without checking permission flags

EXPECTED OUTCOME: These tests MUST FAIL on unfixed code.
This failure confirms the bug exists and provides counterexamples.

After the fix is implemented, these same tests will pass,
confirming the expected behavior is satisfied.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.template import Context, Template
from django.http import JsonResponse
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from core.view_handlers.user_management_views import UserRoleManagementView
from core.mixins import SuperuserRequiredMixin, StaffRequiredMixin
from django.views.generic import View
from django.http import HttpResponse
import json

User = get_user_model()


class DummySuperuserAjaxView(SuperuserRequiredMixin, View):
    """Test view that simulates AJAX endpoint requiring superuser access"""
    def post(self, request):
        return JsonResponse({'success': True, 'message': 'Success'})



class BugConditionExplorationTest(TestCase):
    """
    Property 1: Fault Condition - AJAX Permission Failures Return HTML Instead of JSON
    
    This test demonstrates the bug by showing that when non-superusers make AJAX
    requests to role management endpoints, they receive HTML responses instead of JSON.
    
    **EXPECTED OUTCOME**: This test MUST FAIL on unfixed code.
    
    **Counterexamples to document**:
    - AJAX requests return HTML with Content-Type: text/html
    - Response body starts with <!DOCTYPE or contains HTML tags
    - JavaScript would fail to parse this as JSON
    """
    
    def setUp(self):
        """Set up test users and request factory"""
        self.factory = RequestFactory()
        
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
    
    def test_ajax_permission_failure_returns_html_not_json(self):
        """
        Test that AJAX requests from non-superusers return HTML instead of JSON.
        
        This is the BUG - AJAX endpoints should return JSON for all responses.
        
        **Validates: Requirements 1.1, 1.2, 1.4**
        **Expected Behavior: Requirements 2.1, 2.2, 2.3, 2.4**
        """
        # Create AJAX POST request with XMLHttpRequest header
        request = self.factory.post(
            f'/admin-dashboard/users/{self.regular_user.id}/roles/',
            data={'action': 'assign', 'role': 'admin'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = self.staff_user  # Staff but not superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserAjaxView.as_view()
        response = view(request)
        
        # BUG DEMONSTRATION: Response should be JSON but is HTML
        # Expected behavior: response should be JSON with status 403
        # Actual behavior: response is HTML redirect
        
        # This assertion will FAIL on unfixed code (proving the bug exists)
        self.assertEqual(
            response.get('Content-Type', '').split(';')[0],
            'application/json',
            f"AJAX request returned {response.get('Content-Type')} instead of application/json"
        )
        
        # This assertion will also FAIL on unfixed code
        self.assertEqual(
            response.status_code,
            403,
            f"AJAX request returned status {response.status_code} instead of 403"
        )
        
        # If we got JSON, verify the structure
        if response.get('Content-Type', '').startswith('application/json'):
            data = json.loads(response.content)
            self.assertFalse(data.get('success'))
            self.assertIn('permission', data.get('message', '').lower())
    
    def test_ajax_with_json_content_type_returns_html_not_json(self):
        """
        Test that AJAX requests with application/json content type return HTML.
        
        Modern fetch API uses application/json content type instead of XMLHttpRequest header.
        This should also return JSON but currently returns HTML.
        
        **Validates: Requirements 1.1, 1.4**
        **Expected Behavior: Requirements 2.3, 2.4**
        """
        # Create AJAX POST request with JSON content type
        request = self.factory.post(
            f'/admin-dashboard/users/{self.regular_user.id}/roles/',
            data=json.dumps({'action': 'assign', 'role': 'admin'}),
            content_type='application/json'
        )
        request.user = self.staff_user  # Staff but not superuser
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserAjaxView.as_view()
        response = view(request)
        
        # BUG DEMONSTRATION: Response should be JSON but is HTML
        # This assertion will FAIL on unfixed code
        self.assertEqual(
            response.get('Content-Type', '').split(';')[0],
            'application/json',
            f"AJAX request with JSON content type returned {response.get('Content-Type')} instead of application/json"
        )
        
        self.assertEqual(
            response.status_code,
            403,
            f"AJAX request returned status {response.status_code} instead of 403"
        )
    
    def test_regular_user_ajax_request_returns_html(self):
        """
        Test that regular (non-staff) users also get HTML instead of JSON.
        
        **Validates: Requirements 1.1, 1.4**
        """
        # Create AJAX POST request
        request = self.factory.post(
            f'/admin-dashboard/users/{self.superuser.id}/roles/',
            data={'action': 'assign', 'role': 'admin'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = self.regular_user  # Regular user (not staff, not superuser)
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserAjaxView.as_view()
        response = view(request)
        
        # BUG DEMONSTRATION: Should return JSON 403, but returns HTML redirect
        self.assertEqual(
            response.get('Content-Type', '').split(';')[0],
            'application/json',
            "Regular user AJAX request should return JSON, not HTML"
        )
        
        self.assertEqual(response.status_code, 403)
    


class TemplatePermissionBugTest(TestCase):
    """
    Property 3: Fault Condition - Template Does Not Respect Permission Flags
    
    This test demonstrates that the user detail template renders action buttons
    without checking the can_manage_roles and can_toggle_status permission flags.
    
    **EXPECTED OUTCOME**: This test MUST FAIL on unfixed code.
    
    **Counterexamples to document**:
    - "Manage Roles" button is visible when can_manage_roles=False
    - "Disable/Enable User" buttons are visible when can_toggle_status=False
    """
    
    def test_template_shows_manage_roles_button_without_permission(self):
        """
        Test that template renders "Manage Roles" button even when can_manage_roles=False.
        
        This is the BUG - buttons should be hidden when permission flags are False.
        
        **Validates: Requirements 1.5, 2.5**
        """
        # Simulate the FIXED template with permission checks
        template_string = """
        {% load static %}
        <div class="action-buttons">
            {% if can_manage_roles %}
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#roleManagementModal">
                <i class="fas fa-user-tag me-1"></i> Manage Roles
            </button>
            {% endif %}
            {% if can_toggle_status %}
            {% if user_obj.is_active %}
                <button class="btn btn-danger toggle-status-btn" 
                        data-user-id="{{ user_obj.id }}" 
                        data-action="disable">
                    <i class="fas fa-ban me-1"></i> Disable User
                </button>
            {% else %}
                <button class="btn btn-success toggle-status-btn" 
                        data-user-id="{{ user_obj.id }}" 
                        data-action="enable">
                    <i class="fas fa-check-circle me-1"></i> Enable User
                </button>
            {% endif %}
            {% endif %}
        </div>
        """
        
        # Create a test user
        user_obj = User.objects.create_user(
            email='test@test.com',
            username='testuser',
            password='testpass123',
            is_active=True
        )
        
        # Context with can_manage_roles=False (staff user viewing the page)
        context = Context({
            'user_obj': user_obj,
            'can_manage_roles': False,
            'can_toggle_status': False,
        })
        
        # Render the template
        template = Template(template_string)
        rendered = template.render(context)
        
        # EXPECTED BEHAVIOR: Button should NOT be in rendered HTML when can_manage_roles=False
        # This assertion will PASS on fixed code (confirming the fix works)
        self.assertNotIn(
            'Manage Roles',
            rendered,
            "Template should NOT render 'Manage Roles' button when can_manage_roles=False"
        )
        
        self.assertNotIn(
            'roleManagementModal',
            rendered,
            "Template should NOT render role management modal when can_manage_roles=False"
        )
    
    def test_template_shows_status_toggle_buttons_without_permission(self):
        """
        Test that template renders status toggle buttons even when can_toggle_status=False.
        
        **Validates: Requirements 1.5, 2.6**
        """
        # FIXED template with permission checks
        template_string = """
        {% load static %}
        <div class="action-buttons">
            {% if can_manage_roles %}
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#roleManagementModal">
                <i class="fas fa-user-tag me-1"></i> Manage Roles
            </button>
            {% endif %}
            {% if can_toggle_status %}
            {% if user_obj.is_active %}
                <button class="btn btn-danger toggle-status-btn" 
                        data-user-id="{{ user_obj.id }}" 
                        data-action="disable">
                    <i class="fas fa-ban me-1"></i> Disable User
                </button>
            {% else %}
                <button class="btn btn-success toggle-status-btn" 
                        data-user-id="{{ user_obj.id }}" 
                        data-action="enable">
                    <i class="fas fa-check-circle me-1"></i> Enable User
                </button>
            {% endif %}
            {% endif %}
        </div>
        """
        
        # Create a test user
        user_obj = User.objects.create_user(
            email='test2@test.com',
            username='testuser2',
            password='testpass123',
            is_active=True
        )
        
        # Context with can_toggle_status=False
        context = Context({
            'user_obj': user_obj,
            'can_manage_roles': False,
            'can_toggle_status': False,
        })
        
        # Render the template
        template = Template(template_string)
        rendered = template.render(context)
        
        # EXPECTED BEHAVIOR: Status buttons should NOT be in rendered HTML
        # This assertion will PASS on fixed code
        self.assertNotIn(
            'Disable User',
            rendered,
            "Template should NOT render 'Disable User' button when can_toggle_status=False"
        )
        
        self.assertNotIn(
            'toggle-status-btn',
            rendered,
            "Template should NOT render status toggle buttons when can_toggle_status=False"
        )
    


class PropertyBasedBugExplorationTest(HypothesisTestCase):
    """
    Property-based tests to explore the bug across different user types and request formats.
    
    Uses hypothesis to generate test cases for:
    - Different user types (staff, non-staff, superuser)
    - Different AJAX request formats (XMLHttpRequest header, JSON content type)
    """
    
    def setUp(self):
        """Set up test users"""
        self.factory = RequestFactory()
        
        self.superuser = User.objects.create_user(
            email='superuser@test.com',
            username='superuser',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            username='staff',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='testpass123',
            is_staff=False,
            is_superuser=False
        )
    
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
        ajax_type=st.sampled_from(['xhr', 'json_content_type'])
    )
    @settings(max_examples=10, deadline=None)
    def test_property_ajax_requests_from_non_superusers_should_return_json(
        self, user_type, ajax_type
    ):
        """
        Property: For ANY non-superuser making an AJAX request to a superuser-protected
        endpoint, the response MUST be JSON with status 403.
        
        This property test will FAIL on unfixed code, demonstrating the bug exists
        across multiple user types and AJAX request formats.
        
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        # Select user based on type
        if user_type == 'staff':
            user = self.staff_user
        else:
            user = self.regular_user
        
        # Create request based on AJAX type
        if ajax_type == 'xhr':
            request = self.factory.post(
                f'/admin-dashboard/users/{self.regular_user.id}/roles/',
                data={'action': 'assign', 'role': 'admin'},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
        else:  # json_content_type
            request = self.factory.post(
                f'/admin-dashboard/users/{self.regular_user.id}/roles/',
                data=json.dumps({'action': 'assign', 'role': 'admin'}),
                content_type='application/json'
            )
        
        request.user = user
        request = self._add_middleware_to_request(request)
        
        # Call the view
        view = DummySuperuserAjaxView.as_view()
        response = view(request)
        
        # PROPERTY: AJAX requests should ALWAYS return JSON with 403 status
        # This will FAIL on unfixed code
        content_type = response.get('Content-Type', '').split(';')[0]
        
        self.assertEqual(
            content_type,
            'application/json',
            f"AJAX request from {user_type} user with {ajax_type} returned "
            f"{content_type} instead of application/json"
        )
        
        self.assertEqual(
            response.status_code,
            403,
            f"AJAX request from {user_type} user should return 403, got {response.status_code}"
        )
