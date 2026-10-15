"""Regression coverage for removing an experimental scraper source."""
from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase

from jobs.admin import ScrapedJobAdmin
from jobs.admin_scraper_utils import publish_scraped_job
from jobs.botasaurus_scrapers.orchestrator import SCRAPERS, DEFAULT_SOURCES, scrape_site
from jobs.models import JobPosting, ScrapedJob
from django.contrib import admin


class RetiredSourceConfigurationTests(SimpleTestCase):
    def test_retired_source_is_not_selectable(self):
        self.assertNotIn('PESO_NEGROS_ORIENTAL', SCRAPERS)
        self.assertNotIn('PESO_NEGROS_ORIENTAL', DEFAULT_SOURCES)
        self.assertNotIn('PESO_NEGROS_ORIENTAL', dict(ScrapedJob.SOURCE_CHOICES))
        self.assertIn('PHILJOBNET', SCRAPERS)

    def test_manual_attempt_to_scrape_retired_source_is_rejected(self):
        result = scrape_site('PESO_NEGROS_ORIENTAL', 'nurse', 'Negros Oriental')
        self.assertFalse(result['success'])
        self.assertEqual(result['jobs'], [])
        self.assertIn('Unknown source', result['error'])


class RetiredSourceHistoryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='retired-source-test', email='retired-source@example.org',
            password='test-password-only-2026',
        )
        self.legacy = ScrapedJob.objects.create(
            search_keyword='nurse', search_location='Negros Oriental',
            source='PESO_NEGROS_ORIENTAL', scraped_by=self.user,
            scraped_data={
                'vacancy_leads': [{'title': 'Staff Nurse', 'vacancy_count': 12}],
                'jobs': [{'title': 'Staff Nurse', 'company': 'Unverified Employer',
                          'location': 'Dumaguete'}],
            }, total_found=0, is_active=False,
        )

    def test_retired_historical_record_is_not_publishable(self):
        result = publish_scraped_job(self.legacy, posted_by=self.user)
        self.assertEqual(result['published'], 0)
        self.assertEqual(result['skipped'], 1)
        self.assertFalse(JobPosting.objects.filter(job_title='Staff Nurse').exists())

    def test_retired_records_are_excluded_from_admin_list(self):
        request = RequestFactory().get('/admin/jobs/scrapedjob/')
        request.user = self.user
        model_admin = ScrapedJobAdmin(ScrapedJob, admin.site)
        self.assertFalse(model_admin.get_queryset(request).filter(pk=self.legacy.pk).exists())
