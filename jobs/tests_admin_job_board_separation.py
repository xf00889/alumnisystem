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



class JobAdministrationSeparationTests(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_member_cannot_use_staff_jobs(self):
        from django.core.exceptions import PermissionDenied
        request = self.rf.get(reverse('jobs:admin_job_board'))
        request.user = identity()
        with self.assertRaises(PermissionDenied):
            admin_job_board(request)

    def test_admin_gets_staff_job_board_not_member_page(self):
        request = self.rf.get(reverse('jobs:job_list'))
        request.user = identity(staff=True)
        response = job_list(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('jobs:admin_job_board'))

    def test_anonymous_member_jobs_go_to_landing(self):
        request = self.rf.get(reverse('jobs:job_list'))
        request.user = identity(authenticated=False)
        response = job_list(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:home'))


    def test_administration_cannot_submit_member_application(self):
        from jobs.views import apply_for_job
        request = self.rf.post(reverse('jobs:apply_for_job', kwargs={'slug':'example'}))
        request.user = identity(staff=True)
        response = apply_for_job(request, 'example')
        self.assertEqual(response.status_code, 403)

    def test_staff_or_anon_cannot_query_member_job_modal_json(self):
        from jobs.views import get_job_details
        for user in (identity(staff=True), identity(authenticated=False)):
            request = self.rf.get(reverse('jobs:get_job_details', kwargs={'job_id':1}))
            request.user = user
            self.assertEqual(get_job_details(request, 1).status_code, 403)
