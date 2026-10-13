"""Permission and behavior tests for the shared mentor-circle workflow."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import Mentor, MentorshipRequest
from setup.models import SetupState
from mentorship.models import MentorCircleEntry, MentorCircleMeeting, MentorshipProgress


class MentorCircleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.owner = User.objects.create_user(username='circle_owner', password='long-test-123')
        cls.mentee_a = User.objects.create_user(username='circle_member_a', password='long-test-123')
        cls.mentee_b = User.objects.create_user(username='circle_member_b', password='long-test-123')
        cls.stranger = User.objects.create_user(username='circle_stranger', password='long-test-123')
        cls.pending = User.objects.create_user(username='circle_pending', password='long-test-123')
        cls.mentor = Mentor.objects.create(user=cls.owner, expertise_areas='Software Engineering', is_active=True, accepting_mentees=True)
        def create_for(user, status):
            return MentorshipRequest.objects.create(mentor=cls.mentor, mentee=user, skills_seeking='Programming', goals='Career development', message='Join my cohort', status=status)
        cls.active_a = create_for(cls.mentee_a, 'APPROVED')
        cls.active_b = create_for(cls.mentee_b, 'APPROVED')
        cls.pending_request = create_for(cls.pending, 'PENDING')

    def url(self, endpoint, *args):
        return reverse(f'mentorship:{endpoint}', args=[self.mentor.id, *args])

    def test_group_page_only_for_approved_mentees_and_mentor(self):
        for user in (self.owner, self.mentee_a, self.mentee_b):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url('mentor_circle')).status_code, 200)
        for user in (self.stranger, self.pending):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url('mentor_circle')).status_code, 404)

    def test_message_is_shared_only_with_active_group(self):
        self.client.force_login(self.mentee_a)
        self.assertEqual(self.client.post(self.url('circle_send'), {'content': 'Group update'}).status_code, 200)
        entry = MentorCircleEntry.objects.get(kind='MESSAGE')
        self.assertIsNone(entry.mentorship_id)
        self.client.force_login(self.mentee_b)
        self.assertContains(self.client.get(self.url('circle_activity')), 'Group update')
        self.client.force_login(self.pending)
        self.assertEqual(self.client.get(self.url('circle_activity')).status_code, 404)

    def test_nonmentor_cannot_schedule(self):
        self.client.force_login(self.mentee_a)
        response = self.client.post(self.url('circle_schedule'), {'title': 'Workshop', 'meeting_date': (timezone.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'), 'duration':'60'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(MentorCircleMeeting.objects.count(), 0)

    def test_single_group_meeting_captures_only_approved_attendees(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url('circle_schedule'), {
            'title': 'Portfolio clinic', 'meeting_date': (timezone.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'), 'duration':'60',
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['participants'], 2)
        self.assertEqual(MentorCircleMeeting.objects.count(), 1)
        self.assertEqual(MentorCircleMeeting.objects.get().participants.count(), 2)
        self.assertEqual(MentorCircleEntry.objects.filter(kind='MEETING').count(), 1)

    def test_progress_and_timeline_are_visible_only_to_relevant_mentee(self):
        self.client.force_login(self.owner)
        progress = self.client.post(self.url('circle_update_progress', self.active_a.pk), {'percentage':'45', 'note':'Personal career concern'})
        self.assertEqual(progress.status_code, 200)
        timeline = self.client.post(self.url('circle_update_timeline', self.active_a.pk), {
            'period[]':['1–2'], 'description[]':['Private milestone'], 'status[]':['IN_PROGRESS']
        })
        self.assertEqual(timeline.status_code, 200)
        self.active_a.refresh_from_db()
        self.assertEqual(self.active_a.progress_percentage, 45)
        self.assertIn('Private milestone', self.active_a.timeline_milestones)
        self.assertEqual(MentorshipProgress.objects.filter(mentorship=self.active_a).count(), 1)
        self.assertTrue(MentorCircleEntry.objects.filter(kind='PROGRESS', mentorship=self.active_a).exists())
        self.client.force_login(self.mentee_a)
        self.assertContains(self.client.get(self.url('circle_activity')), 'Private milestone')
        self.assertContains(self.client.get(self.url('circle_activity')), 'Personal career concern')
        self.client.force_login(self.mentee_b)
        page = self.client.get(self.url('circle_activity'))
        self.assertNotContains(page, 'Private milestone')
        self.assertNotContains(page, 'Personal career concern')

    def test_invalid_and_unrelated_progress_cannot_change_records(self):
        self.client.force_login(self.mentee_a)
        self.assertEqual(self.client.post(self.url('circle_update_progress', self.active_a.pk), {'percentage':'50', 'note':'Wrong role'}).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.url('circle_update_progress', self.active_a.pk), {'percentage':'105', 'note':'Wrong range'}).status_code, 400)
        self.assertEqual(self.client.post(self.url('circle_update_progress', self.pending_request.pk), {'percentage':'50', 'note':'Pending'}).status_code, 404)

    def test_csrf_protected_group_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.url('circle_send'), {'content':'Hi'}).status_code, 403)

    def test_meeting_cancelled_by_owner_not_mentee(self):
        self.client.force_login(self.owner)
        date = (timezone.now()+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.client.post(self.url('circle_schedule'), {'title':'Group workshop', 'meeting_date':date, 'duration':45})
        meeting = MentorCircleMeeting.objects.get()
        url = self.url('circle_cancel_meeting', meeting.pk)
        self.client.force_login(self.mentee_a)
        self.assertEqual(self.client.post(url).status_code, 403)
        meeting.refresh_from_db()
        self.assertFalse(meeting.is_cancelled)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url).status_code, 200)
        meeting.refresh_from_db()
        self.assertTrue(meeting.is_cancelled)
        self.assertEqual(self.client.post(url).status_code, 409)

    def test_personal_meeting_cancel_keeps_record_and_logs_private_event(self):
        from mentorship.models import MentorshipMeeting
        meeting = MentorshipMeeting.objects.create(
            mentorship=self.active_a, title='Career check-in',
            meeting_date=timezone.now()+timedelta(days=2), status='SCHEDULED',
        )
        url = reverse('mentorship:cancel_personal_meeting', args=[meeting.pk])
        self.client.force_login(self.mentee_a)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url).status_code, 200)
        meeting.refresh_from_db()
        self.assertEqual(meeting.status, 'CANCELLED')
        self.client.force_login(self.mentee_a)
        self.assertContains(self.client.get(self.url('circle_activity')), 'Career check-in')
        self.client.force_login(self.mentee_b)
        self.assertNotContains(self.client.get(self.url('circle_activity')), 'Career check-in')

    def test_user_loses_group_access_after_mentorship_ends(self):
        self.client.force_login(self.mentee_a)
        self.assertEqual(self.client.get(self.url('mentor_circle')).status_code, 200)
        self.active_a.status = 'COMPLETED'
        self.active_a.save(update_fields=['status'])
        self.assertEqual(self.client.get(self.url('mentor_circle')).status_code, 404)
        self.assertEqual(self.client.post(self.url('circle_send'), {'content':'No access'}).status_code, 404)
