"""Regression checks for privileged admin routes and member-only entry points.

Run from project root: python manage.py test alumni_groups.tests_admin_directory_separation jobs.tests_admin_job_board_separation
"""
from types import SimpleNamespace
from django.test import SimpleTestCase, RequestFactory
from django.urls import reverse, resolve
from alumni_groups.views import GroupListView, AdminGroupDirectoryView
from jobs.views import job_list, job_detail
from jobs.admin_directory_views import admin_job_board, admin_job_details


def identity(*, staff=False, authenticated=True):
    return SimpleNamespace(
        is_authenticated=authenticated,
        is_staff=staff,
        is_superuser=False,
        profile=SimpleNamespace(is_alumni_coordinator=False, is_hr=False),
    )



class GroupAdministrationSeparationTests(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_admin_and_member_routes_use_different_views(self):
        self.assertIs(resolve(reverse('alumni_groups:admin_group_directory')).func.view_class, AdminGroupDirectoryView)
        self.assertIs(resolve(reverse('alumni_groups:group_list')).func.view_class, GroupListView)
        self.assertIs(resolve(reverse('jobs:admin_job_board')).func, admin_job_board)
        self.assertIs(resolve(reverse('jobs:job_list')).func, job_list)

    def test_member_cannot_open_admin_group_directory(self):
        request = self.rf.get(reverse('alumni_groups:admin_group_directory'))
        request.user = identity()
        with self.assertRaises(Exception) as exc:
            AdminGroupDirectoryView.as_view()(request)
        from django.core.exceptions import PermissionDenied
        self.assertIsInstance(exc.exception, PermissionDenied)

    def test_admin_is_redirected_out_of_member_group_directory(self):
        request = self.rf.get(reverse('alumni_groups:group_list'))
        request.user = identity(staff=True)
        response = GroupListView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('alumni_groups:admin_group_directory'))

    def test_no_join_or_apply_buttons_in_staff_templates(self):
        from pathlib import Path
        groups = Path('templates/alumni_groups/admin/group_directory.html').read_text()
        jobs = Path('jobs/templates/jobs/admin/job_board.html').read_text()
        self.assertNotIn("alumni_groups:join_group", groups)
        self.assertNotIn("jobs:apply_for_job", jobs)

