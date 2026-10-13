"""Regression tests for mentor dashboard accept/reject behavior."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.middleware.csrf import _get_new_csrf_string
from accounts.models import Mentor, MentorshipRequest
from setup.models import SetupState


class MentorRequestDecisionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.mentor_user = User.objects.create_user(username='mentor_decision', password='testpass123')
        cls.other_user = User.objects.create_user(username='unrelated_decision', password='testpass123')
        cls.mentee = User.objects.create_user(username='mentee_decision', password='testpass123')
        cls.mentor = Mentor.objects.create(
            user=cls.mentor_user, expertise_areas='Data Analysis, Web Developer',
            is_active=True, accepting_mentees=True,
        )

    def setUp(self):
        self.mentorship = MentorshipRequest.objects.create(
            mentor=self.mentor, mentee=self.mentee, skills_seeking='Python',
            goals='Build a portfolio', message='Please mentor me', status='PENDING',
        )
        self.url = reverse('mentorship:update_request_status', args=[self.mentorship.pk])
        self.client.force_login(self.mentor_user)

    def test_mentor_can_accept_pending_request(self):
        result = self.client.post(self.url, {'status': 'APPROVED'}, HTTP_ACCEPT='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['status'], 'APPROVED')
        self.mentorship.refresh_from_db()
        self.assertEqual(self.mentorship.status, 'APPROVED')

    def test_mentor_can_reject_pending_request(self):
        result = self.client.post(self.url, {'status': 'REJECTED'}, HTTP_ACCEPT='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['status'], 'REJECTED')
        self.mentorship.refresh_from_db()
        self.assertEqual(self.mentorship.status, 'REJECTED')

    def test_unrelated_user_cannot_review_request(self):
        self.client.force_login(self.other_user)
        result = self.client.post(self.url, {'status': 'APPROVED'})
        self.assertEqual(result.status_code, 403)
        self.assertEqual(result['Content-Type'], 'application/json')
        self.mentorship.refresh_from_db()
        self.assertEqual(self.mentorship.status, 'PENDING')

    def test_invalid_decision_does_not_change_request(self):
        result = self.client.post(self.url, {'status': 'COMPLETED'})
        self.assertEqual(result.status_code, 400)
        self.mentorship.refresh_from_db()
        self.assertEqual(self.mentorship.status, 'PENDING')

    def test_duplicate_decision_is_conflict_not_double_review(self):
        self.client.post(self.url, {'status': 'APPROVED'})
        second = self.client.post(self.url, {'status': 'REJECTED'})
        self.assertEqual(second.status_code, 409)
        self.mentorship.refresh_from_db()
        self.assertEqual(self.mentorship.status, 'APPROVED')

    def test_dashboard_buttons_render_named_status_url(self):
        result = self.client.get(reverse('mentorship:mentor_dashboard'))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, f'data-mentorship-status-url="{self.url}"', count=2)
        self.assertNotContains(result, '/mentorship/requests/1/update_status/')

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.mentor_user)
        self.assertEqual(client.post(self.url, {'status': 'APPROVED'}).status_code, 403)
        token = _get_new_csrf_string()
        client.cookies['csrftoken'] = token
        result = client.post(self.url, {'status': 'APPROVED'}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(result.status_code, 200)
