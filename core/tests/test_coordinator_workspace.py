"""Coordinator role boundary, campus validation and dashboards."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from core.models.coordinator_campus import CoordinatorCampus
from core.services.user_management import RoleAssignmentService
from alumni_directory.models import Alumni
from unittest.mock import patch

@override_settings(
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STORAGES={'default': {'BACKEND':'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}},
)
class CoordinatorAccessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_guard=patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        cls.addClassCleanup(setup_guard.stop)
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.root = U.objects.create_superuser(username='coord-root', email='root-coord@example.net',password='temporaryStrongPass123!')
        cls.coordinator = U.objects.create_user(username='campus-coordinator', email='coordinator@example.net',password='temporaryStrongPass123!')
        cls.coordinator.profile.is_alumni_coordinator = True
        cls.coordinator.profile.save(update_fields=['is_alumni_coordinator'])
        CoordinatorCampus.objects.create(user=cls.coordinator,campus='MAIN')
    def test_workspace_shows_only_assigned_campuses_and_charts(self):
        self.client.force_login(self.coordinator)
        r=self.client.get(reverse('core:coordinator_dashboard'))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'coordinator-campus-data')
        self.assertContains(r,'Dumaguete Main Campus')
        self.assertNotContains(r, 'Bayawan-Sta. Catalina Campus')
    def test_coordinator_uses_hr_style_top_navigation_on_workspace_pages(self):
        self.client.force_login(self.coordinator)
        for route in ('core:coordinator_dashboard', 'accounts:staff_profile'):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Alumni Coordinator navigation')
                self.assertContains(response, 'class="hr-topbar coordinator-topbar"')
                self.assertContains(response, 'Coordinator Workspace')
                self.assertNotContains(response, 'class="staff-sidebar"')
                self.assertNotContains(response, 'Manage Jobs')
                self.assertNotContains(response, 'System Settings')
        dashboard = self.client.get(reverse('core:coordinator_dashboard'))
        self.assertContains(dashboard, 'aria-current="page"')

    def test_top_navigation_groups_match_allowed_sidebar_sections(self):
        self.client.force_login(self.coordinator)
        response = self.client.get(reverse('core:coordinator_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="coordinator-primary-nav"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'coordinator-menu-popover')
        self.assertContains(response, 'js/admin/coordinator-navigation.js')
        html = response.content.decode()
        self.assertEqual(html.count('<details class="coordinator-menu-group'), 6)
        for group in ('Alumni Management', 'Communications', 'Donations',
                      'Mentorship', 'Analytics', 'Account'):
            with self.subTest(group=group):
                self.assertIn('>'+group+' <i class="fas fa-chevron-down"', html)
        for destination in ('alumni_directory:alumni_list',
                            'alumni_groups:admin_group_directory',
                            'location_tracking:map', 'feedback:manage_feedbacks',
                            'donations:manage_campaigns',
                            'accounts:admin_mentor_list', 'surveys:report_list',
                            'accounts:staff_profile'):
            with self.subTest(destination=destination):
                self.assertIn('href="'+reverse(destination)+'"', html)
        for excluded in ('Manage Jobs', 'User Management', 'System Controls',
                         'Scrape PH Job Sites'):
            self.assertNotIn('>'+excluded+'<', html)

    def test_restricted_system_and_job_routes_are_blocked(self):
        self.client.force_login(self.coordinator)
        self.assertEqual(self.client.get(reverse('jobs:manage_jobs')).status_code,403)
        self.assertEqual(self.client.get(reverse('core:user_list')).status_code,403)
        self.assertEqual(self.client.get(reverse('core:system_settings')).status_code,403)
        self.assertRedirects(self.client.get(reverse('core:admin_dashboard')),reverse('core:coordinator_dashboard'),fetch_redirect_response=False)
    def test_role_requires_valid_campus_and_no_privilege_escalation(self):
        U=get_user_model()
        target=U.objects.create_user(username='campus-new',email='campus-new@example.net',password='temporaryStrongPass123!')
        self.assertFalse(RoleAssignmentService.assign_role(target,'alumni_coordinator',self.root,campus_codes=[],send_email=False)[0])
        self.assertFalse(target.profile.is_alumni_coordinator)
        self.assertFalse(RoleAssignmentService.assign_role(target,'alumni_coordinator',self.root,campus_codes=['INVALID'],send_email=False)[0])
        self.assertTrue(RoleAssignmentService.assign_role(target,'alumni_coordinator',self.root,campus_codes=['MAIN','BSC'],send_email=False)[0])
        target.refresh_from_db(); target.profile.refresh_from_db()
        self.assertTrue(target.profile.is_alumni_coordinator)
        self.assertFalse(target.is_staff)
        self.assertEqual(set(CoordinatorCampus.objects.filter(user=target).values_list('campus', flat=True)),{'MAIN','BSC'})
        self.assertTrue(RoleAssignmentService.remove_role(target,'alumni_coordinator',self.root,send_email=False)[0])
        self.assertFalse(CoordinatorCampus.objects.filter(user=target).exists())
    def test_non_coordinators_cannot_access_coordinator_dashboard(self):
        self.client.force_login(self.root)
        self.assertEqual(self.client.get(reverse('core:coordinator_dashboard')).status_code,403)
