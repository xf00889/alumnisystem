"""Regression guard: HR charts use portal applications, not external-only applications."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from jobs.models import JobApplication, JobPosting


@override_settings(SECURE_SSL_REDIRECT=False)
class HRDashboardDistributionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        guard.start()
        cls.addClassCleanup(guard.stop)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.hr = User.objects.create_user(username='analytics-hr', password='StrongPass!2026')
        cls.hr.profile.is_hr = True
        cls.hr.profile.is_alumni_coordinator = False
        cls.hr.profile.save(update_fields=['is_hr', 'is_alumni_coordinator'])
        seeker_a = User.objects.create_user(username='analytics-seeker-a', password='StrongPass!2026')
        seeker_b = User.objects.create_user(username='analytics-seeker-b', password='StrongPass!2026')
        cls.portal = JobPosting.objects.create(job_title='Portal Role', company_name='NORSU', location='Main',
                                               job_description='Test', source_type='INTERNAL', job_type='FULL_TIME')
        cls.external = JobPosting.objects.create(job_title='External Role', company_name='Other', location='Remote',
                                                 job_description='Test', source_type='EXTERNAL', job_type='REMOTE',
                                                 application_link='https://example.net/apply')
        JobApplication.objects.create(job=cls.portal, applicant=seeker_a, resume='test/one.pdf', status='SHORTLISTED')
        # Historic external-only data must not appear in HR portal application counts.
        JobApplication.objects.create(job=cls.external, applicant=seeker_b, resume='test/two.pdf', status='PENDING')

    def test_hr_charts_are_derived_from_actual_portal_records(self):
        self.client.force_login(self.hr)
        response = self.client.get(reverse('jobs:hr_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['submitted_applications'], 1)
        self.assertEqual(sum(response.context['status_chart']['values']), 1)
        self.assertEqual(response.context['positions_chart']['labels'], ['Portal Role'])
        self.assertEqual(response.context['positions_chart']['values'], [1])
        self.assertEqual(sum(response.context['types_chart']['values']), 2)
        self.assertContains(response, 'hr-status-data')
        self.assertContains(response, 'admin-page-header')
