"""
Test script to verify Alumni Coordinator permissions are correctly restricted.

This script tests that:
1. Alumni Coordinators can access the user detail page
2. Alumni Coordinators cannot see the "Manage Roles" button
3. Alumni Coordinators cannot access the role management endpoint
4. Superusers can access everything
"""

import os
import sys
import django

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import Profile

User = get_user_model()


class AlumniCoordinatorPermissionsTest(TestCase):
    """Test Alumni Coordinator permission restrictions"""
    
    def setUp(self):
        """Create test users"""
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='superuser@test.com',
            email='superuser@test.com',
            password='testpass123',
            first_name='Super',
            last_name='User'
        )
        
        # Create alumni coordinator
        self.coordinator = User.objects.create_user(
            username='coordinator@test.com',
            email='coordinator@test.com',
            password='testpass123',
            first_name='Alumni',
            last_name='Coordinator',
            is_staff=True  # Coordinators need staff access
        )
        self.coordinator.profile.is_alumni_coordinator = True
        self.coordinator.profile.save()
        
        # Create regular user to manage
        self.regular_user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password='testpass123',
            first_name='Regular',
            last_name='User'
        )
        
        self.client = Client()
    
    def test_coordinator_can_access_user_detail(self):
        """Alumni Coordinators should be able to view user details"""
        self.client.login(username='coordinator@test.com', password='testpass123')
        
        url = reverse('core:user_detail', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        print("✓ Alumni Coordinator can access user detail page")
    
    def test_coordinator_cannot_see_manage_roles_button(self):
        """Alumni Coordinators should NOT see the Manage Roles button"""
        self.client.login(username='coordinator@test.com', password='testpass123')
        
        url = reverse('core:user_detail', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        # Check context variable
        self.assertFalse(response.context['can_manage_roles'])
        
        # Check button is not in HTML
        self.assertNotContains(response, 'Manage Roles')
        self.assertNotContains(response, 'roleManagementModal')
        
        print("✓ Alumni Coordinator cannot see Manage Roles button")
    
    def test_coordinator_cannot_access_role_management_endpoint(self):
        """Alumni Coordinators should get 403 when trying to manage roles"""
        self.client.login(username='coordinator@test.com', password='testpass123')
        
        url = reverse('core:user_role_management', kwargs={'pk': self.regular_user.pk})
        response = self.client.post(
            url,
            data={'action': 'assign', 'role': 'hr'},
            content_type='application/json'
        )
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        print("✓ Alumni Coordinator gets 403 when accessing role management endpoint")
    
    def test_superuser_can_see_manage_roles_button(self):
        """Superusers should see the Manage Roles button"""
        self.client.login(username='superuser@test.com', password='testpass123')
        
        url = reverse('core:user_detail', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        # Check context variable
        self.assertTrue(response.context['can_manage_roles'])
        
        # Check button is in HTML
        self.assertContains(response, 'Manage Roles')
        self.assertContains(response, 'roleManagementModal')
        
        print("✓ Superuser can see Manage Roles button")
    
    def test_superuser_can_access_role_management_endpoint(self):
        """Superusers should be able to manage roles"""
        self.client.login(username='superuser@test.com', password='testpass123')
        
        url = reverse('core:user_role_management', kwargs={'pk': self.regular_user.pk})
        response = self.client.post(
            url,
            data={'action': 'assign', 'role': 'hr'},
            content_type='application/json'
        )
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        print("✓ Superuser can access role management endpoint")
    
    def test_coordinator_context_flags(self):
        """Verify all permission flags are correct for Alumni Coordinator"""
        self.client.login(username='coordinator@test.com', password='testpass123')
        
        url = reverse('core:user_detail', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        
        context = response.context
        
        # These should be False for coordinators
        self.assertFalse(context['is_superuser'])
        self.assertFalse(context['can_modify_user'])
        self.assertFalse(context['can_manage_roles'])
        self.assertFalse(context['can_toggle_status'])
        
        print("✓ All permission flags are correctly set to False for Alumni Coordinator")


def run_tests():
    """Run the tests and print results"""
    import sys
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    failures = test_runner.run_tests(['__main__'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    # Run tests
    run_tests()
