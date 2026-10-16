"""Security and delivery regression tests for opt-in web push."""
import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from core.models import Notification, NotificationPreference, WebPushDelivery, WebPushSubscription
from core.web_push import queue_web_push, safe_target_url, payload_for_notification
from core.web_push_views import _endpoint_valid

GOOD_ENDPOINT = 'https://fcm.googleapis.com/fcm/send/sample-endpoint'
CREDENTIALS = {'endpoint': GOOD_ENDPOINT, 'keys': {'p256dh': 'A' * 88, 'auth': 'B' * 24}}
VAPID = {'WEB_PUSH_VAPID_PUBLIC_KEY': 'dummy-public', 'WEB_PUSH_VAPID_PRIVATE_KEY': 'dummy-private',
         'WEB_PUSH_VAPID_SUBJECT': 'mailto:alumni@example.org'}


@override_settings(SECURE_SSL_REDIRECT=False, **VAPID)
class WebPushTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='alumni_push_one', password='TestPass!2026')
        cls.other = get_user_model().objects.create_user(username='alumni_push_two', password='TestPass!2026')

    def test_endpoint_blocks_server_side_request_forgery(self):
        for endpoint in ('http://fcm.googleapis.com/xx','https://127.0.0.1:8000/admin/',
                         'https://intranet.example.com/','https://evil.fcm.googleapis.com.example.net/',
                         'https://fcm.googleapis.com.evil.invalid/'):
            self.assertFalse(_endpoint_valid(endpoint))
        self.assertTrue(_endpoint_valid(GOOD_ENDPOINT))

    def test_anonymous_and_csrf_protections(self):
        endpoint = reverse('pwa_push_subscribe')
        self.assertIn(self.client.post(endpoint, data=json.dumps(CREDENTIALS), content_type='application/json').status_code, (302,403))
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post(endpoint, data=json.dumps(CREDENTIALS), content_type='application/json').status_code,403)

    def test_subscribe_rebind_and_unsubscribe_only_owner(self):
        self.client.force_login(self.user)
        url = reverse('pwa_push_subscribe')
        self.assertEqual(self.client.post(url, data=json.dumps(CREDENTIALS), content_type='application/json').status_code, 200)
        self.assertEqual(WebPushSubscription.objects.count(), 1)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, data=json.dumps(CREDENTIALS), content_type='application/json').status_code, 200)
        self.assertEqual(WebPushSubscription.objects.get().user_id, self.other.pk)
        self.client.force_login(self.user)
        self.client.post(reverse('pwa_push_unsubscribe'), data=json.dumps({'endpoint':GOOD_ENDPOINT}), content_type='application/json')
        self.assertEqual(WebPushSubscription.objects.count(), 1)
        self.client.force_login(self.other)
        self.client.post(reverse('pwa_push_unsubscribe'), data=json.dumps({'endpoint':GOOD_ENDPOINT}), content_type='application/json')
        self.assertFalse(WebPushSubscription.objects.exists())

    def test_notification_enqueued_once_and_no_content_leak(self):
        sub = WebPushSubscription.objects.create(user=self.user, **{
            'endpoint': GOOD_ENDPOINT, 'p256dh': 'A'*88, 'auth': 'B'*24})
        alert = Notification.create_notification(recipient=self.user, notification_type='new_message',
            title='Private message', message='CONFIDENTIAL CONTENT', action_url='https://evil.example/phish')
        queue_web_push(alert.pk)
        queue_web_push(alert.pk)
        self.assertEqual(WebPushDelivery.objects.filter(notification=alert, subscription=sub).count(),1)
        payload = payload_for_notification(alert)
        self.assertNotIn('CONFIDENTIAL', payload)
        self.assertNotIn('evil.example', payload)

    def test_in_app_preference_suppresses_push(self):
        WebPushSubscription.objects.create(user=self.user,endpoint=GOOD_ENDPOINT,p256dh='A'*88,auth='B'*24)
        NotificationPreference.objects.create(user=self.user, app_messages=False)
        note = Notification.create_notification(recipient=self.user, notification_type='new_message', title='X',message='Y')
        queue_web_push(note.pk)
        self.assertFalse(WebPushDelivery.objects.exists())

    def test_standalone_launch_logged_in_uses_existing_home(self):
        # The test database has an incomplete setup state by default.
        # Model a configured installation without bypassing setup in production.
        self.client.force_login(self.user)
        with patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True):
            self.assertRedirects(
                self.client.get(reverse('pwa_launch')),
                reverse('core:home'),
                fetch_redirect_response=False,
            )

    def test_standalone_launch_still_respects_incomplete_setup(self):
        self.client.force_login(self.user)
        with patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=False):
            self.assertRedirects(
                self.client.get(reverse('pwa_launch')),
                reverse('setup:welcome'),
                fetch_redirect_response=False,
            )

    def test_announcement_push_targets_only_matching_subscribers(self):
        from announcements.models import Announcement
        from core.web_push import queue_published_announcement
        WebPushSubscription.objects.create(user=self.user, endpoint=GOOD_ENDPOINT, p256dh='A'*88, auth='B'*24)
        WebPushSubscription.objects.create(user=self.other,
            endpoint='https://fcm.googleapis.com/fcm/send/different', p256dh='A'*88, auth='B'*24)
        announcement = Announcement.objects.create(title='Alumni update', content='Test update',
                                                   target_audience='COLLEGE', target_value='CCS')
        # The audience resolver, NOT the subscription list, decides recipients.
        with patch('announcements.audience.announcement_recipients') as audience:
            audience.return_value = get_user_model().objects.filter(pk=self.user.pk)
            queue_published_announcement(announcement.pk)
        sent_to = list(Notification.objects.filter(notification_type='announcement').values_list('recipient_id',flat=True))
        self.assertEqual(sent_to, [self.user.pk])
        self.assertEqual(WebPushDelivery.objects.filter(notification__notification_type='announcement').count(),1)

    def test_safe_path(self):
        self.assertEqual(safe_target_url('/announcements/'), '/announcements/')
        self.assertNotEqual(safe_target_url('//evil.example'), '//evil.example')
        self.assertNotEqual(safe_target_url('/\\evil.example'), '/\\evil.example')
