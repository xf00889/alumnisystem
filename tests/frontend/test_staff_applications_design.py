"""Offline implementation checks for the staff Job Applications page.

These do not replace Django integration tests or an authenticated browser test.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = (ROOT / 'jobs/templates/jobs/manage_applications.html').read_text()
CSS = (ROOT / 'static/css/admin/job-applications.css').read_text()


class StaffApplicationsDesignTests(unittest.TestCase):
    def test_static_manifest_reference_is_not_regressed(self):
        self.assertNotIn("css/job_applications.css", TEMPLATE)
        self.assertIn("css/modules/jobs-app.css", TEMPLATE)
        self.assertIn("css/admin/job-applications.css", TEMPLATE)

    def test_template_is_admin_facing(self):
        self.assertIn("{% url 'jobs:admin_job_board' %}", TEMPLATE)
        self.assertIn('ADMINISTRATION / CAREER SERVICES', TEMPLATE)
        self.assertIn('staff-applications-page', TEMPLATE)

    def test_status_counts_are_django_bound(self):
        for status in ('pending', 'shortlisted', 'interviewed', 'accepted'):
            self.assertIn('{{ stats.%s }}' % status, TEMPLATE)

    def test_applicant_workflows_retained(self):
        for token in ('status-select', 'data-view-application', 'data-add-note',
                      'applicationModal', 'noteModal', 'applicationDetails',
                      'application.resume.url', 'application.additional_documents.url',
                      'jobs:update_application_status', 'jobs:application_details',
                      'showEmailModal', 'window.addNote', 'window.viewApplication'):
            self.assertIn(token, TEMPLATE)

    def test_ajax_requests_include_server_required_header(self):
        self.assertIn("'X-Requested-With':'XMLHttpRequest'", TEMPLATE)
        self.assertIn("'X-CSRFToken':csrfToken", TEMPLATE)

    def test_filters_and_pagination_retained(self):
        for token in ('status_choices', '?status=', 'applications.has_previous',
                      'applications.has_next', 'applications.paginator.page_range'):
            self.assertIn(token, TEMPLATE)

    def test_template_tags_balanced(self):
        tags = re.findall(r'{%\s*(if|endif|for|endfor|block|endblock)\b', TEMPLATE)
        openers = [t for t in tags if t in ('if', 'for', 'block')]
        closers = [t for t in tags if t in ('endif', 'endfor', 'endblock')]
        self.assertEqual(len(openers), len(closers))

    def test_responsive_and_scoped_css(self):
        self.assertIn('html.fe-page--app-jobs-jobs-manage-applications-html', CSS)
        self.assertIn('@media (max-width:700px)', CSS)
        self.assertIn('.staff-applications-table-wrap', CSS)


if __name__ == '__main__':
    unittest.main()
