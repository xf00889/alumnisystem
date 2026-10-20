"""Directory uses a compact authorized handoff, not embedded employability queries."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni


@override_settings(MIDDLEWARE=[m for m in settings.MIDDLEWARE
                              if m != 'setup.middleware.SetupRequiredMiddleware'])
class DirectoryReportNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user(
            username='staff-navigation', email='staff-navigation@example.com',
            password='testpass', is_staff=True,
        )
        cls.member = User.objects.create_user(
            username='member-navigation', email='member-navigation@example.com',
            password='testpass',
        )
        Alumni.objects.create(
            user=cls.member, campus='BSC', college='CTE', course='BEED',
            graduation_year=2025, gender='F', province='Negros Oriental',
            city='Bayawan', address='Test',
        )

    def test_selected_directory_scope_handoffs_to_dedicated_report(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('alumni_directory:alumni_list'), {
            'graduation_year': '2025', 'college': 'CTE',
            'course': 'BEED', 'campus': 'BSC',
        }, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Employability Report')
        self.assertContains(response, 'action="' + reverse('surveys:employability_report') + '"')
        for key, value in [('cohort_year','2025'), ('college','CTE'),
                           ('course','BEED'), ('campus','BSC')]:
            self.assertContains(response, 'name="%s" value="%s"' % (key,value))
        self.assertNotContains(response, 'directoryEmployabilityForm')
        self.assertNotContains(response, 'alumni-employability.js')
        self.assertNotContains(response, 'alumni-employability.css')
        self.assertNotContains(response, 'Export report:')

    def test_no_year_does_not_send_fake_cohort(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('alumni_directory:alumni_list'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Employability Report')
        self.assertNotContains(response, 'name="cohort_year"')

    def test_regular_alumnus_does_not_see_staff_reporting_action(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('alumni_directory:alumni_list'), {
            'search': 'member'
        }, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'View Employability Report')
