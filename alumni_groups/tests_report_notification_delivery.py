"""Report moderation should notify the reporting alumnus in the global notification bell."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models.notifications import Notification
from .models import AlumniGroup, GroupMembership, Post, PostReport


class ReportNotificationDeliveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username='moderation_admin', password='test', is_staff=True)
        cls.reporter = User.objects.create_user(username='moderation_reporter', password='test')
        cls.outsider = User.objects.create_user(username='moderation_outsider', password='test')
        cls.group = AlumniGroup.objects.create(
            name='Moderation Notice Test', description='test', group_type='MANUAL',
            visibility='PRIVATE', created_by=cls.admin,
        )
        for user, role in ((cls.admin, 'ADMIN'), (cls.reporter, 'MEMBER')):
            GroupMembership.objects.create(group=cls.group, user=user, role=role, status='APPROVED')
        cls.post = Post.objects.create(
            group=cls.group, author=cls.admin, content='Moderation test post', status='APPROVED',
        )

    def create_report(self):
        return PostReport.objects.create(post=self.post, reporter=self.reporter, reason='Possible spam')

    def review(self, report, **data):
        return self.client.post(
            reverse('alumni_groups:review_report', kwargs={'report_id': report.pk}), data
        )

    def test_approved_report_delivers_one_system_notification(self):
        report = self.create_report()
        self.client.force_login(self.admin)
        self.assertEqual(self.review(report, action='resolve').status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, 'RESOLVED')
        notice = Notification.objects.get(recipient=self.reporter)
        self.assertEqual(notice.notification_type, 'system')
        self.assertIn('approved', notice.title.lower())
        self.assertFalse(notice.is_read)
        self.assertEqual(notice.sender_id, self.admin.pk)
        self.assertEqual(notice.action_url, reverse('core:all_notifications'))
        self.review(report, action='resolve')
        self.assertEqual(Notification.objects.filter(recipient=self.reporter).count(), 1)

    def test_rejected_report_notifies_with_reason(self):
        report = self.create_report()
        self.client.force_login(self.admin)
        self.assertEqual(self.review(report, action='dismiss', resolution_note='Not a violation').status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, 'DISMISSED')
        notice = Notification.objects.get(recipient=self.reporter)
        self.assertIn('rejected', notice.title.lower())
        self.assertIn('Not a violation', notice.message)

    def test_approve_and_remove_post_notifies_reporter(self):
        report = self.create_report()
        self.client.force_login(self.admin)
        self.assertEqual(self.review(report, action='remove_post').status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'REJECTED')
        self.assertIn('removed', Notification.objects.get(recipient=self.reporter).message.lower())

    def test_invalid_or_unauthorized_review_does_not_notify(self):
        report = self.create_report()
        self.client.force_login(self.reporter)
        self.assertEqual(self.review(report, action='resolve').status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.review(report, action='dismiss', resolution_note='').status_code, 400)
        self.assertEqual(self.review(report, action='unexpected').status_code, 400)
        self.assertFalse(Notification.objects.filter(recipient=self.reporter).exists())
        report.refresh_from_db()
        self.assertEqual(report.status, 'OPEN')

    def test_notification_is_visible_in_global_inbox(self):
        report = self.create_report()
        self.client.force_login(self.admin)
        self.review(report, action='resolve')
        self.client.force_login(self.reporter)
        response = self.client.get(reverse('core:all_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your group post report was approved')
