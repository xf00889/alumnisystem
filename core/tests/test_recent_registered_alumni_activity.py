"""Dashboard recent-registration feed must exclude unverified/uncompleted signups."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni

TEST_MIDDLEWARE = [m for m in settings.MIDDLEWARE
                   if m != 'setup.middleware.SetupRequiredMiddleware']


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class RecentRegisteredAlumniActivityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username='activity-admin', password='StrongPass123!', is_staff=True, is_superuser=True
        )
        self.pending = User.objects.create_user(
            username='pending-enrollment', password='StrongPass123!'
        )
        self.account_only = User.objects.create_user(
            username='profile-flag-only', password='StrongPass123!'
        )
        self.account_only.profile.has_completed_registration = True
        self.account_only.profile.save(update_fields=['has_completed_registration'])
        self.completed = User.objects.create_user(
            username='completed-alumni', password='StrongPass123!'
        )
        self.completed.profile.has_completed_registration = True
        self.completed.profile.save(update_fields=['has_completed_registration'])
        Alumni.objects.create(
            user=self.completed, campus='BSC', college='CTE', course='BEED',
            graduation_year=2025, gender='F', province='Negros Oriental',
            city='Bayawan', address='Test',
        )

    def test_recent_activity_includes_only_completed_alumni_records(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('core:admin_dashboard'), secure=True)
        self.assertEqual(response.status_code, 200)
        recent = list(response.context['recent_users'])
        self.assertEqual([person.pk for person in recent], [self.completed.pk])
        self.assertContains(response, 'New Registered Alumni')
        self.assertNotContains(response, 'pending-enrollment')
        self.assertNotContains(response, 'profile-flag-only')
