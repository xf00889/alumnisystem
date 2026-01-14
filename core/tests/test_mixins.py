"""
Tests for permission mixins in core.mixins module.

These tests verify that SuperuserRequiredMixin and StaffRequiredMixin
properly restrict access and log unauthorized attempts.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.views.generic import View
from django.http import HttpResponse
from core.mixins import SuperuserRequiredMixin, StaffRequiredMixin
import logging

User = get_user_model()


class DummySuperuserView(SuperuserRequiredMixin, View):
    """Test view that requires superuser access"""
    def get(self, request):
        return HttpResponse("Success")


class DummyStaffView(StaffRequiredMixin, View):
    """Test view that requires staff access"""
    def get(self, request):
        return HttpResponse("Success")


class SuperuserRequiredMixinTest(TestCase):
    """Test cases for SuperuserRequiredMixin"""
    
    def setUp(self):
        """Set up test users and request factory"""
        self.factory = RequestFactory()
        
        # Create test users
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
        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_superuser_can_access(self):
        """Test that superusers can access the view"""
        request = self.factory.get('/test/')
        request.user = self.superuser
        request = self._add_middleware_to_request(request)
        
        view = DummySuperuserView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_staff_user_cannot_access(self):
        """Test that staff users (non-superuser) cannot access the view"""
        request = self.factory.get('/test/')
        request.user = self.staff_user
        request = self._add_middleware_to_request(request)
        
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # Should redirect to admin dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('admin-dashboard', response.url)
    
    def test_regular_user_cannot_access(self):
        """Test that regular users cannot access the view"""
        request = self.factory.get('/test/')
        request.user = self.regular_user
        request = self._add_middleware_to_request(request)
        
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # Should redirect to admin dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('admin-dashboard', response.url)
    
    def test_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request = self._add_middleware_to_request(request)
        
        view = DummySuperuserView.as_view()
        response = view(request)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class StaffRequiredMixinTest(TestCase):
    """Test cases for StaffRequiredMixin"""
    
    def setUp(self):
        """Set up test users and request factory"""
        self.factory = RequestFactory()
        
        # Create test users
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
        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_superuser_can_access(self):
        """Test that superusers can access the view"""
        request = self.factory.get('/test/')
        request.user = self.superuser
        request = self._add_middleware_to_request(request)
        
        view = DummyStaffView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_staff_user_can_access(self):
        """Test that staff users can access the view"""
        request = self.factory.get('/test/')
        request.user = self.staff_user
        request = self._add_middleware_to_request(request)
        
        view = DummyStaffView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_regular_user_cannot_access(self):
        """Test that regular users cannot access the view"""
        request = self.factory.get('/test/')
        request.user = self.regular_user
        request = self._add_middleware_to_request(request)
        
        view = DummyStaffView.as_view()
        response = view(request)
        
        # Should redirect to admin dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('admin-dashboard', response.url)
    
    def test_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request = self._add_middleware_to_request(request)
        
        view = DummyStaffView.as_view()
        response = view(request)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class MixinLoggingTest(TestCase):
    """Test cases for logging functionality in mixins"""
    
    def setUp(self):
        """Set up test users and request factory"""
        self.factory = RequestFactory()
        
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
        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_superuser_mixin_logs_unauthorized_access(self):
        """Test that SuperuserRequiredMixin logs unauthorized access attempts"""
        with self.assertLogs('core', level='WARNING') as cm:
            request = self.factory.get('/test/')
            request.user = self.staff_user
            request = self._add_middleware_to_request(request)
            
            view = DummySuperuserView.as_view()
            response = view(request)
            
            # Check that warning was logged
            self.assertTrue(any('Unauthorized superuser access attempt' in log for log in cm.output))
            self.assertTrue(any('staff@test.com' in log for log in cm.output))
    
    def test_staff_mixin_logs_unauthorized_access(self):
        """Test that StaffRequiredMixin logs unauthorized access attempts"""
        with self.assertLogs('core', level='WARNING') as cm:
            request = self.factory.get('/test/')
            request.user = self.regular_user
            request = self._add_middleware_to_request(request)
            
            view = DummyStaffView.as_view()
            response = view(request)
            
            # Check that warning was logged
            self.assertTrue(any('Unauthorized staff access attempt' in log for log in cm.output))
            self.assertTrue(any('user@test.com' in log for log in cm.output))
