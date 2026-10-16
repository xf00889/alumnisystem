"""Coverage for career-only HR access and internal application boundaries."""
import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import Profile
from jobs.models import JobPosting, JobApplication

@override_settings(SECURE_SSL_REDIRECT=False)
class HRWorkspaceAndApplicationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        guard=patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        guard.start()
        cls.addClassCleanup(guard.stop)

    @classmethod
    def setUpTestData(cls):
        User=get_user_model()
        cls.hr=User.objects.create_user(username='hr_role_test', password='VeryStrongPass!2026', email='hr-test@example.org')
        profile,_=Profile.objects.get_or_create(user=cls.hr)
        profile.is_hr=True
        profile.is_alumni_coordinator=False
        profile.save(update_fields=['is_hr','is_alumni_coordinator'])
        cls.alumni=User.objects.create_user(username='jobseeker_test',password='VeryStrongPass!2026',email='seeker-test@example.org')
        cls.external=JobPosting.objects.create(job_title='External Job',company_name='Third Party',location='Remote',job_description='External application only',source_type='EXTERNAL',application_link='https://example.org/apply',accepts_internal_applications=False)
        cls.internal=JobPosting.objects.create(job_title='Internal Job',company_name='NORSU',location='Dumaguete',job_description='Apply through the portal',source_type='INTERNAL')

    def test_hr_is_not_staff_and_receives_limited_dashboard(self):
        self.assertFalse(self.hr.is_staff)
        self.client.force_login(self.hr)
        response=self.client.get(reverse('jobs:hr_dashboard'))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'HR Overview')
        self.assertContains(response,'My Profile')
        self.assertNotContains(response,'Donation Verification')
        self.assertEqual(self.client.get(reverse('jobs:manage_jobs')).status_code,200)
        self.assertEqual(self.client.get(reverse('accounts:staff_profile')).status_code,200)
        self.assertEqual(self.client.get(reverse('jobs:post_job')).status_code,200)
        self.assertEqual(self.client.get(reverse('jobs:admin_job_board')).status_code,200)
        self.assertNotEqual(self.client.get(reverse('core:admin_dashboard')).status_code,200)
        self.assertNotEqual(self.client.get(reverse('jobs:scraper_dashboard')).status_code,200)

    def test_non_hr_cannot_open_hr_dashboard(self):
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.get(reverse('jobs:hr_dashboard')).status_code,403)
        self.assertNotEqual(self.client.get(reverse('jobs:manage_jobs')).status_code,200)

    def test_external_posting_has_no_application_management_ui_or_route(self):
        self.client.force_login(self.hr)
        listing=self.client.get(reverse('jobs:manage_jobs'))
        self.assertContains(listing,'External site')
        self.assertNotContains(listing,reverse('jobs:manage_applications',args=[self.external.slug]))
        self.assertContains(listing,reverse('jobs:manage_applications',args=[self.internal.slug]))
        self.assertEqual(self.client.get(reverse('jobs:manage_applications',args=[self.external.slug])).status_code,404)
        self.assertEqual(self.client.get(reverse('jobs:manage_applications',args=[self.internal.slug])).status_code,200)
        details=self.client.get(reverse('jobs:admin_job_details',args=[self.external.slug]))
        self.assertNotContains(details,reverse('jobs:manage_applications',args=[self.external.slug]))

    def test_jobseeker_can_apply_internally_with_uploaded_resume(self):
        self.client.force_login(self.alumni)
        self.assertTrue(self.internal.accepts_internal_applications)
        with patch('jobs.forms.is_recaptcha_enabled',return_value=False):
            page=self.client.get(reverse('jobs:apply_for_job', args=[self.internal.slug]))
            self.assertEqual(page.status_code,200)
            submitted=self.client.post(reverse('jobs:apply_for_job',args=[self.internal.slug]),{
                'cover_letter':'Please review my application',
                'resume':SimpleUploadedFile('resume.pdf',b'%PDF-1.4\nresume content',content_type='application/pdf'),
            })
        self.assertEqual(submitted.status_code,302)
        self.assertTrue(JobApplication.objects.filter(job=self.internal,applicant=self.alumni).exists())
        with patch('jobs.ai_matching.get_ai_match_score', return_value=None):
            duplicate=self.client.get(reverse('jobs:job_detail', args=[self.internal.slug]))
        self.assertContains(duplicate,'Application Submitted')

    def test_eligibility_does_not_allow_third_party_applications(self):
        self.client.force_login(self.alumni)
        external=self.client.get(reverse('jobs:check_job_application_eligibility',args=[self.external.pk]))
        self.assertFalse(external.json()['eligible'])
        internal=self.client.get(reverse('jobs:check_job_application_eligibility',args=[self.internal.pk]))
        self.assertTrue(internal.json()['eligible'])
