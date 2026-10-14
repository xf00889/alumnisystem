"""Offline source-level checks for isolated admin UX components.

Run from project root: python -m unittest tests.frontend.test_staff_directory_ui_source
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AdminDirectorySourceTests(unittest.TestCase):
    def test_modules_parse(self):
        for filename in (
            'jobs/admin_directory_views.py',
            'core/templatetags/admin_directory_pagination.py',
            'jobs/tests_admin_job_board_ui.py',
        ):
            ast.parse((ROOT / filename).read_text(encoding='utf-8'))

    def test_staff_views_retained_and_stable_ordering(self):
        source = (ROOT / 'jobs/admin_directory_views.py').read_text(encoding='utf-8')
        self.assertIn('is_hr_or_admin(request.user)', source)
        self.assertIn("order_by('-posted_date', '-pk')", source)
        self.assertIn("params.pop('page', None)", source)

    def test_pages_do_not_render_member_actions(self):
        for name in ('job_board.html', 'job_details.html'):
            source = (ROOT / 'jobs/templates/jobs/admin' / name).read_text(encoding='utf-8')
            self.assertNotIn('jobs:apply_for_job', source)
            self.assertNotIn('jobs:job_detail', source)

    def test_job_details_has_real_metadata_and_management_actions(self):
        source = (ROOT / 'jobs/templates/jobs/admin/job_details.html').read_text(encoding='utf-8')
        for value in ('job.responsibilities', 'job.requirements', 'job.benefits',
                      'job.get_experience_level_display', 'jobs:edit_job',
                      'jobs:manage_applications'):
            self.assertIn(value, source)

    def test_shared_pagination_both_pages(self):
        for page in ('jobs/templates/jobs/admin/job_board.html',
                     'templates/alumni_groups/admin/group_directory.html'):
            source = (ROOT / page).read_text(encoding='utf-8')
            self.assertIn('load static admin_directory_pagination', source)
            self.assertIn('admin_directory_pagination ', source)
            self.assertIn('staff-directory-results', source)
        template = (ROOT / 'templates/admin/components/directory_pagination.html').read_text(encoding='utf-8')
        for expected in ('aria-current="page"', 'has_previous', 'has_next', 'page_numbers', 'filters_query'):
            self.assertIn(expected, template)

    def test_group_admin_actions_preserved(self):
        source = (ROOT / 'templates/alumni_groups/admin/group_directory.html').read_text(encoding='utf-8')
        self.assertIn('admin_group_actions.html', source)
        self.assertIn('admin_group_modals.html', source)
        self.assertNotIn('alumni_groups:join_group', source)


if __name__ == '__main__':
    unittest.main()
