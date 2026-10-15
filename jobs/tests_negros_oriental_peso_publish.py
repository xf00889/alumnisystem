"""Django database tests for PESO vacancy-lead publication safeguards."""
# Database-level guard is validated by Django tests on the VPS.
from django.test import TestCase
from jobs.admin_scraper_utils import publish_scraped_job
from jobs.models import ScrapedJob, JobPosting
from django.contrib.auth import get_user_model


class PESOPublicationGuardTests(TestCase):
    def test_office_summary_cannot_be_published_even_if_json_contains_jobs(self):
        User = get_user_model()
        user = User.objects.create_user(username='peso-review-admin', email='peso-review@example.org', password='safe-test-only-password')
        record = ScrapedJob.objects.create(
            search_keyword='nurse', search_location='Negros Oriental', source='PESO_NEGROS_ORIENTAL',
            scraped_by=user, scraped_data={
                'vacancy_leads': [{'title': 'STAFF NURSE', 'vacancy_count': 72}],
                'jobs': [{'title':'STAFF NURSE', 'company':'Imaginary Employer', 'location':'Dumaguete'}],
            },
            total_found=0,
        )
        self.assertEqual(publish_scraped_job(record, posted_by=user)['published'], 0)
        self.assertFalse(JobPosting.objects.filter(job_title='STAFF NURSE').exists())
