"""Dependency-free source contracts for alumni job board application CTAs."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class FeaturedInternalApplicationContracts(unittest.TestCase):
    def test_featured_card_exposes_internal_apply_and_job_details(self):
        template = (ROOT / 'jobs/templates/jobs/job_list.html').read_text(encoding='utf-8')
        featured = template.split('<!-- Featured Jobs Section -->', 1)[1].split('<!-- All Jobs Section -->', 1)[0]
        self.assertIn("{% url 'jobs:apply_for_job' job.slug %}", featured)
        self.assertIn("{% url 'jobs:job_detail' job.slug %}", featured)
        self.assertIn('job.accepts_internal_applications', featured)
        self.assertIn('job.has_applied', featured)

    def test_ajax_results_respect_external_and_existing_applications(self):
        template = (ROOT / 'jobs/templates/jobs/partials/job_list_results.html').read_text(encoding='utf-8')
        self.assertIn('job.has_applied', template)
        self.assertIn('Applied · View Status', template)
        self.assertIn('job.application_link', template)
        self.assertIn("{% url 'jobs:apply_for_job' job.slug %}", template)

    def test_application_flag_is_a_query_annotation(self):
        views = (ROOT / 'jobs/views.py').read_text(encoding='utf-8')
        self.assertIn('has_applied=Exists(', views)
        self.assertIn("applicant_id=request.user.pk", views)
        self.assertIn("job_id=OuterRef('pk')", views)
        self.assertIn('if job.accepts_internal_applications:', views)


if __name__ == '__main__':
    unittest.main()
