"""Regression coverage for group joining and membership question safeguards."""
import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import AlumniGroup, GroupMembership, SecurityQuestion, SecurityQuestionAnswer


class GroupSecurityQuestionWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username='questions-admin', password='test-password')
        cls.applicant = User.objects.create_user(username='questions-applicant', password='test-password')
        cls.group = AlumniGroup.objects.create(
            name='Question Protected Alumni Group', description='Example',
            group_type='MANUAL', visibility='PRIVATE', course='IT',
            requires_approval=True, has_security_questions=True, created_by=cls.admin,
        )
        GroupMembership.objects.create(group=cls.group, user=cls.admin, role='ADMIN', status='APPROVED')
        cls.question = SecurityQuestion.objects.create(group=cls.group, question='What batch did you attend?', is_required=True)

    def join_url(self):
        return reverse('alumni_groups:join_group', kwargs={'slug': self.group.slug})

    def approve_url(self, membership):
        return reverse('alumni_groups:update_member_status', kwargs={'membership_id': membership.pk})

    def test_get_never_creates_membership_and_shows_question_form(self):
        self.client.force_login(self.applicant)
        response = self.client.get(self.join_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question)
        self.assertFalse(GroupMembership.objects.filter(group=self.group, user=self.applicant).exists())

    def test_required_answers_are_validated_before_membership_is_created(self):
        self.client.force_login(self.applicant)
        response = self.client.post(self.join_url(), {f'question_{self.question.pk}': ' '})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GroupMembership.objects.filter(group=self.group, user=self.applicant).exists())

    def test_submission_saves_questions_and_waits_for_approval(self):
        self.client.force_login(self.applicant)
        response = self.client.post(self.join_url(), {f'question_{self.question.pk}': 'Batch 2025'})
        self.assertEqual(response.status_code, 302)
        membership = GroupMembership.objects.get(group=self.group, user=self.applicant)
        self.assertEqual(membership.status, 'PENDING')
        self.assertEqual(membership.security_answers.get(question=self.question).answer, 'Batch 2025')

    def test_legacy_pending_request_can_complete_missing_answers(self):
        membership = GroupMembership.objects.create(group=self.group, user=self.applicant, status='PENDING')
        self.client.force_login(self.applicant)
        response = self.client.get(self.join_url())
        self.assertEqual(response.status_code, 200)
        self.client.post(self.join_url(), {f'question_{self.question.pk}': 'Batch 2023'})
        self.assertEqual(GroupMembership.objects.filter(group=self.group, user=self.applicant).count(), 1)
        self.assertTrue(SecurityQuestionAnswer.objects.filter(membership=membership, question=self.question).exists())

    def test_admin_cannot_approve_missing_required_answers(self):
        membership = GroupMembership.objects.create(group=self.group, user=self.applicant, status='PENDING')
        self.client.force_login(self.admin)
        response = self.client.post(self.approve_url(membership), data=json.dumps({'action': 'approve'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'PENDING')
        self.assertIn('answers', response.json()['message'].lower())

    def test_legacy_questions_route_uses_same_guard(self):
        self.client.force_login(self.applicant)
        response = self.client.get(reverse('alumni_groups:join_group_with_questions', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GroupMembership.objects.filter(group=self.group, user=self.applicant).exists())

    def test_blocked_membership_cannot_be_recreated(self):
        GroupMembership.objects.create(group=self.group, user=self.applicant, status='BLOCKED', is_active=False)
        self.client.force_login(self.applicant)
        self.client.post(self.join_url(), {f'question_{self.question.pk}': 'Bypass attempt'})
        membership = GroupMembership.objects.get(group=self.group, user=self.applicant)
        self.assertEqual(membership.status, 'BLOCKED')
