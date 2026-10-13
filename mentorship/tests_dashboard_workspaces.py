"""Regression tests for mentor/mentee workspace navigation and approved membership."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from accounts.models import Mentor, MentorshipRequest
from mentorship.models import MentorshipProgress
from setup.models import SetupState


class DashboardWorkspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.owner = User.objects.create_user(username='dashboard_mentor', password='safe-pass-123')
        cls.mentee = User.objects.create_user(username='dashboard_mentee', password='safe-pass-123')
        cls.pending = User.objects.create_user(username='dashboard_applicant', email='private-mentee@example.invalid', password='safe-pass-123')
        cls.stranger = User.objects.create_user(username='dashboard_stranger', password='safe-pass-123')
        cls.mentor = Mentor.objects.create(user=cls.owner, expertise_areas='Software Engineering', is_active=True)
        cls.active = MentorshipRequest.objects.create(
            mentor=cls.mentor, mentee=cls.mentee, skills_seeking='Web apps',
            goals='Publish a portfolio', message='I need career guidance', status='APPROVED',
        )
        cls.application = MentorshipRequest.objects.create(
            mentor=cls.mentor, mentee=cls.pending, skills_seeking='Python',
            goals='Learn software testing', message='Applying to learn', status='PENDING',
        )

    def test_mentor_more_link_is_conditional(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('mentorship:mentor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mentor dashboard')
        self.assertContains(response, 'View mentee details')
        self.assertContains(response, 'End mentorship')
        self.client.force_login(self.mentee)
        response = self.client.get(reverse('mentorship:mentee_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mentee dashboard')
        self.assertNotContains(response, '>Mentor dashboard</span>')

    def test_mentee_dashboard_uses_group_workspace_without_legacy_composer(self):
        self.client.force_login(self.mentee)
        response = self.client.get(reverse('mentorship:mentee_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('mentorship:mentor_circle', args=[self.mentor.pk]))
        self.assertContains(response, 'Mentorship workspaces')
        self.assertNotContains(response, 'onclick="sendMessage(')

    def test_protected_applicant_preview(self):
        url = reverse('mentorship:mentor_mentee_details', args=[self.application.pk])
        self.client.force_login(self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Learn software testing')
        self.assertContains(response, 'Python')
        self.assertNotContains(response, 'private-mentee@example.invalid')
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.pending)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_only_owner_can_end_mentorship_and_records_are_preserved(self):
        url = reverse('mentorship:mentor_end_mentorship', args=[self.active.pk])
        self.client.force_login(self.mentee)
        self.assertEqual(self.client.post(url, {'reason':'Mentoring engagement completed early.'}).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url, {'reason':'short'}).status_code, 400)
        self.assertEqual(self.client.post(url, {'reason':'Mentoring engagement completed early.'}).status_code, 200)
        self.active.refresh_from_db()
        self.assertEqual(self.active.status, 'CANCELLED')
        self.assertEqual(MentorshipProgress.objects.filter(mentorship=self.active).count(), 1)
        self.assertEqual(self.client.post(url, {'reason':'Try again after ending.'}).status_code, 409)
        self.client.force_login(self.mentee)
        self.assertEqual(self.client.get(reverse('mentorship:mentor_circle', args=[self.mentor.pk])).status_code, 404)
        dashboard = self.client.get(reverse('mentorship:mentee_dashboard'))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'Previous mentorships')
        self.assertContains(dashboard, 'Publish a portfolio')

    def test_applicant_can_withdraw_pending_request(self):
        url = reverse('mentorship:mentee_withdraw_request', args=[self.application.pk])
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.pending)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'CANCELLED')
        self.assertEqual(self.client.post(url).status_code, 409)

    def test_csrf_blocks_untrusted_end_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(
            reverse('mentorship:mentor_end_mentorship', args=[self.active.pk]),
            {'reason':'Testing an untrusted request attempt.'},
        ).status_code, 403)
