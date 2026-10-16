"""Layout and upload regressions for the alumni job application workflow."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from jobs.forms import JobApplicationForm
from jobs.models import JobApplication, JobApplicationDocument, JobPosting, RequiredDocument


@override_settings(SECURE_SSL_REDIRECT=False)
class AlumniJobApplicationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        cls.addClassCleanup(setup_guard.stop)

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        media = override_settings(MEDIA_ROOT=folder.name)
        media.enable()
        self.addCleanup(media.disable)
        captcha = patch('jobs.forms.is_recaptcha_enabled', return_value=False)
        captcha.start()
        self.addCleanup(captcha.stop)

        self.user = get_user_model().objects.create_user(
            username='application_seeker', password='StrongPassword!2026',
            email='seeker@example.org',
        )
        self.client.force_login(self.user)
        self.job = JobPosting.objects.create(
            job_title='Career Adviser', company_name='NORSU', location='Dumaguete',
            job_description='Help graduates', source_type='INTERNAL',
            accepts_internal_applications=True,
        )
        self.first = RequiredDocument.objects.create(
            job=self.job, name='Transcript', document_type='TRANSCRIPT',
            is_required=True, file_types='.pdf', max_file_size=5120,
        )
        self.second = RequiredDocument.objects.create(
            job=self.job, name='Diploma', document_type='DIPLOMA',
            is_required=True, file_types='.pdf,.docx', max_file_size=5120,
        )
        self.url = reverse('jobs:apply_for_job', args=[self.job.slug])

    @staticmethod
    def file(name, size=100):
        return SimpleUploadedFile(name, b'x' * size, content_type='application/octet-stream')

    def payload(self):
        return {
            'cover_letter': 'I am interested in this position.',
            'resume': self.file('resume.pdf'),
            f'document_{self.first.pk}': self.file('transcript.pdf'),
            f'document_{self.second.pk}': self.file('diploma.pdf'),
            'additional_documents': self.file('portfolio.pdf'),
        }

    def test_compact_layout_renders_bound_required_file_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'job-application-hero')
        self.assertContains(response, 'alumni-job-application')
        self.assertContains(response, 'Submit Application')
        self.assertContains(response, f'name="document_{self.first.pk}"')
        self.assertContains(response, f'name="document_{self.second.pk}"')
        self.assertContains(response, 'name="resume"')
        self.assertContains(response, 'name="additional_documents"')

    def test_submission_preserves_each_document_and_optional_file(self):
        response = self.client.post(self.url, self.payload())
        self.assertRedirects(response, reverse('jobs:job_detail', args=[self.job.slug]))
        application = JobApplication.objects.get(applicant=self.user, job=self.job)
        self.assertTrue(application.resume.name.endswith('.pdf'))
        self.assertTrue(application.additional_documents.name.endswith('portfolio.pdf'))
        files = list(JobApplicationDocument.objects.filter(application=application))
        self.assertEqual(len(files), 2)
        self.assertEqual({f.requirement_id for f in files}, {self.first.id, self.second.id})
        self.assertEqual({f.name for f in files}, {'Transcript', 'Diploma'})
        self.assertTrue(all(Path(folder.file.path).is_file() for folder in files))

    def test_missing_required_file_shows_validation_and_creates_no_application(self):
        payload = self.payload()
        payload.pop(f'document_{self.first.pk}')
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Some information needs attention')
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_invalid_file_types_and_sizes_are_rejected(self):
        payload = self.payload()
        payload[f'document_{self.first.pk}'] = self.file('wrong.docx')
        payload[f'document_{self.second.pk}'] = self.file('too-big.pdf', size=6000)
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please upload a file of type: .pdf')
        self.assertContains(response, 'Maximum file size')
        self.assertFalse(JobApplication.objects.exists())

    def test_optional_requirement_does_not_block_submission(self):
        self.second.is_required = False
        self.second.save(update_fields=['is_required'])
        payload = self.payload()
        payload.pop(f'document_{self.second.pk}')
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
        application = JobApplication.objects.get(applicant=self.user, job=self.job)
        self.assertEqual(application.required_document_files.count(), 1)

    def test_resume_rejects_unsupported_format(self):
        form = JobApplicationForm(data={'cover_letter': 'Hello'}, files={
            'resume': self.file('resume.exe'),
            f'document_{self.first.pk}': self.file('transcript.pdf'),
            f'document_{self.second.pk}': self.file('diploma.pdf'),
        }, job=self.job)
        self.assertFalse(form.is_valid())
        self.assertIn('resume', form.errors)
