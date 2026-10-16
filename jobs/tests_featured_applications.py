"""Regression checks for internal apply actions on featured and normal job cards."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from jobs.models import JobApplication, JobPosting


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class FeaturedJobApplicationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        guard.start()
        cls.addClassCleanup(guard.stop)

    @classmethod
    def setUpTestData(cls):
        cls.alumni = get_user_model().objects.create_user(
            username='featured_job_seeker', email='featured-job@example.org', password='StrongPassword!2026'
        )
        cls.internal = JobPosting.objects.create(
            job_title='Internal Featured Role', company_name='NORSU', location='Dumaguete',
            job_description='Open to alumni', source_type='INTERNAL', is_featured=True,
        )
        cls.external = JobPosting.objects.create(
            job_title='External Featured Role', company_name='Partner Employer', location='Remote',
            job_description='Employer handles application', source_type='EXTERNAL', is_featured=True,
            accepts_internal_applications=False, application_link='https://example.org/jobs/apply',
        )

    def setUp(self):
        self.client.force_login(self.alumni)
        self.ai_disabled = patch('jobs.views._get_ai_sort_state', return_value=(False, 0))
        self.ai_disabled.start()
        self.addCleanup(self.ai_disabled.stop)

    def test_featured_internal_job_shows_real_apply_button(self):
        response = self.client.get(reverse('jobs:job_list'), {'sort': 'latest'})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        featured = html.split('<!-- Featured Jobs Section -->', 1)[1].split('<!-- All Jobs Section -->', 1)[0]
        self.assertIn(reverse('jobs:apply_for_job', args=[self.internal.slug]), featured)
        self.assertIn('Apply Now', featured)
        self.assertIn(reverse('jobs:job_detail', args=[self.internal.slug]), featured)
        self.assertIn('View Details', featured)
        with patch('jobs.forms.is_recaptcha_enabled', return_value=False):
            form = self.client.get(reverse('jobs:apply_for_job', args=[self.internal.slug]))
        self.assertEqual(form.status_code, 200)
        self.assertContains(form, 'Submit Application')

    def test_external_featured_job_does_not_offer_portal_apply(self):
        response = self.client.get(reverse('jobs:job_list'), {'sort': 'latest'})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        featured = html.split('<!-- Featured Jobs Section -->', 1)[1].split('<!-- All Jobs Section -->', 1)[0]
        self.assertNotIn(reverse('jobs:apply_for_job', args=[self.external.slug]), featured)
        self.assertIn('https://example.org/jobs/apply', featured)
        self.assertIn('Apply on External Site', featured)

    def test_applied_job_shows_status_not_duplicate_apply(self):
        JobApplication.objects.create(
            job=self.internal, applicant=self.alumni,
            resume='job_applications/resumes/existing.pdf',
        )
        response = self.client.get(reverse('jobs:job_list'), {'sort': 'latest'})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        featured = html.split('<!-- Featured Jobs Section -->', 1)[1].split('<!-- All Jobs Section -->', 1)[0]
        self.assertIn('Application submitted', featured)
        self.assertNotIn(reverse('jobs:apply_for_job', args=[self.internal.slug]), featured)
        self.assertIn('Applied · View Status', html)
        with patch('jobs.ai_matching.get_ai_match_score', return_value=None):
            detail = self.client.get(reverse('jobs:job_detail', args=[self.internal.slug]))
        self.assertContains(detail, 'Application Submitted')

    def test_ajax_job_cards_preserve_application_actions(self):
        response = self.client.get(
            reverse('jobs:job_list'), {'sort': 'latest', 'partial': 'jobs'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        markup = response.json()['jobs_html']
        self.assertIn(reverse('jobs:apply_for_job', args=[self.internal.slug]), markup)
        self.assertNotIn(reverse('jobs:apply_for_job', args=[self.external.slug]), markup)
