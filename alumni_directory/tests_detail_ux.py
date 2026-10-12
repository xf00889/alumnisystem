"""Alumni Detail privacy and UX regressions for the 2026 profile refresh."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Alumni
from connections.models import Connection
from setup.models import SetupState


class AlumniDetailProfileUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Skip installation wizard redirects in an otherwise fresh test database.
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.owner = User.objects.create_user(username='profile_owner_ux', password='test-password', first_name='Sample', last_name='Graduate')
        cls.viewer = User.objects.create_user(username='profile_viewer_ux', password='test-password')
        cls.alumni = Alumni.objects.create(
            user=cls.owner,
            college='CIT', campus='MAIN', course='Private Academic Program',
            graduation_year=2020, gender='O', province='Private Province', city='Private City',
            address='Private Home Address', bio='Private professional biography',
            current_company='Private Employer', job_title='Private Role',
            skills='Python, Django', interests='Mentorship, Community', is_verified=True,
        )

    def profile_url(self):
        return reverse('alumni_directory:alumni_detail', args=[self.alumni.pk])

    def test_regular_alumnus_sees_useful_but_privacy_restricted_profile(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.profile_url())
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('Connect with your community', html)
        self.assertIn('Profile privacy', html)
        self.assertIn('Sample Graduate', html)
        self.assertNotIn('Private Academic Program', html)
        self.assertNotIn('Private professional biography', html)
        self.assertNotIn('Private Employer', html)
        self.assertNotIn('Private Home Address', html)
        self.assertNotIn('Private Province', html)
        self.assertIn('Connect', html)

    def test_profile_owner_sees_career_and_academic_information(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.profile_url())
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('Private Academic Program', html)
        self.assertIn('Private professional biography', html)
        self.assertIn('Private Employer', html)
        self.assertIn('Update your profile', html)
        self.assertIn('Python', html)
        self.assertIn('Django', html)

    def test_staff_sees_academic_information(self):
        User = get_user_model()
        staff = User.objects.create_user(username='staff_detail_ux', password='test-password', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(self.profile_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Private Academic Program')

    def test_profile_connection_actions_use_app_modal_not_browser_confirm(self):
        # Profile-side actions were previously triggering browser-native confirms
        # and a second request through the global connection click handler.
        Connection.objects.create(requester=self.viewer, receiver=self.owner, status='ACCEPTED')
        self.client.force_login(self.viewer)
        response = self.client.get(self.profile_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'remove-connection-btn')
        self.assertContains(response, 'confirmProfileConnection')
        self.assertContains(response, 'Remove connection?')
        self.assertNotContains(response, "if (confirm('Are you sure you want to remove")
        self.assertNotContains(response, "if (confirm('Are you sure you want to reject")
