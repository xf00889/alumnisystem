"""Source and route regression contracts for the staff Manage Jobs workspace."""
from pathlib import Path
from django.test import SimpleTestCase
from django.urls import resolve, reverse

ROOT = Path(__file__).resolve().parents[1]


class ManageJobsDirectoryContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = (ROOT / 'jobs/templates/jobs/manage_jobs.html').read_text(encoding='utf-8')

    def test_manage_jobs_uses_staff_table_not_old_card_grid(self):
        self.assertIn('staff-directory-table', self.template)
        self.assertIn('staff-group-directory--manage-jobs', self.template)
        self.assertNotIn('class="jobs-grid"', self.template)

    def test_application_actions_use_existing_job_specific_route(self):
        self.assertIn("{% url 'jobs:manage_applications' job.slug %}", self.template)
        self.assertIn('Manage Applications', self.template)
        self.assertIn('job.application_count', self.template)

    def test_with_applications_filter_preserves_pagination(self):
        self.assertIn('applications=with', self.template)
        self.assertIn('jobs_with_applications', self.template)
        self.assertIn("Count('applications', distinct=True)", (ROOT/'jobs/views.py').read_text(encoding='utf-8'))

    def test_existing_crud_controls_and_permissions_are_preserved(self):
        self.assertIn("{% url 'jobs:post_job' %}", self.template)
        self.assertIn("{% url 'jobs:edit_job' job.slug %}", self.template)
        self.assertIn("{% url 'jobs:delete_job' job.slug %}", self.template)
        self.assertIn("{% url 'jobs:admin_job_details' job.slug %}", self.template)
        self.assertTrue(reverse('jobs:manage_jobs').startswith('/jobs/'))

    def test_deletion_requires_post_with_csrf_and_confirmation(self):
        script = (ROOT/'static/js/admin/manage-jobs.js').read_text(encoding='utf-8')
        self.assertIn("method: 'POST'", script)
        self.assertIn("'X-CSRFToken'", script)
        self.assertIn('showCancelButton: true', script)
        self.assertNotIn('onclick="confirmDelete(', self.template)

    def test_mobile_logo_has_no_decorative_container(self):
        style = (ROOT/'static/css/alumni/navigation.css').read_text(encoding='utf-8')
        self.assertIn('alumni-nav-brand--mobile .alumni-brand-symbol', style)
        self.assertIn('background:transparent;border:0;border-radius:0;box-shadow:none;padding:0;', style)
