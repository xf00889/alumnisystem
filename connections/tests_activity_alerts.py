"""Regression tests for connection requests, message notices and activity counts."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Notification, NotificationPreference
from setup.models import SetupState
from .models import Connection, DirectConversation, DirectMessage


class ActivityAlertsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Requests in this suite must reach the connection/notification views.
        # A fresh test database otherwise triggers SetupRequiredMiddleware's
        # normal redirect to the installation wizard instead of returning JSON.
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.alice = User.objects.create_user(username='activity_alice', password='strong-123')
        cls.bob = User.objects.create_user(username='activity_bob', password='strong-123')
        cls.charlie = User.objects.create_user(username='activity_charlie', password='strong-123')

    def test_request_notifies_recipient_and_count_is_private(self):
        self.client.force_login(self.alice)
        url = reverse('connections:send_request', args=[self.bob.pk])
        self.assertTrue(self.client.post(url).json()['success'])
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='connection_request').count(), 1)
        self.assertFalse(self.client.post(url).json()['success'])
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='connection_request').count(), 1)
        self.assertEqual(self.client.get(reverse('connections:activity_summary')).json()['pending_requests'], 0)
        self.client.force_login(self.bob)
        response = self.client.get(reverse('connections:activity_summary'))
        self.assertEqual(response.json()['pending_requests'], 1)
        self.assertEqual(response.json()['notifications'][0]['notification_type'], 'connection_request')

    def test_accepting_request_notifies_sender_and_clears_receiver_alert(self):
        connection = Connection.objects.create(requester=self.alice, receiver=self.bob, status='PENDING')
        Notification.create_notification(recipient=self.bob, sender=self.alice,
            notification_type='connection_request', title='Request', message='Please connect',
            content_object=connection, action_url=reverse('connections:connection_requests'))
        self.client.force_login(self.bob)
        self.assertTrue(self.client.post(reverse('connections:accept_request', args=[connection.pk])).json()['success'])
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='connection_request', is_read=False).count(), 0)
        self.assertEqual(self.client.get(reverse('connections:activity_summary')).json()['pending_requests'], 0)
        notification = Notification.objects.get(recipient=self.alice, notification_type='connection_accepted')
        self.assertEqual(notification.sender, self.bob)

    def test_direct_message_signal_notifies_once_and_opening_chat_clears_it(self):
        connection = Connection.objects.create(requester=self.alice, receiver=self.bob, status='ACCEPTED')
        conversation = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        message = DirectMessage.objects.create(conversation=conversation, sender=self.alice, content='Hi Bob!')
        message.content = 'Edited'; message.save()
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='new_message').count(), 1)
        self.assertFalse(Notification.objects.filter(recipient=self.alice, notification_type='new_message').exists())
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse('connections:activity_summary')).json()['unread_messages'], 1)
        self.client.get(reverse('connections:direct_messages', args=[self.alice.pk]))
        self.assertEqual(self.client.get(reverse('connections:activity_summary')).json()['unread_messages'], 0)

    def test_group_message_notifies_other_participants(self):
        conversation = DirectConversation.create_group_chat(
            self.alice, [self.bob, self.charlie], 'Class Reunion'
        )
        DirectMessage.objects.create(conversation=conversation, sender=self.alice, content='Meeting soon')
        notices = Notification.objects.filter(notification_type='new_message')
        recipients = set(notices.values_list('recipient_id', flat=True))
        self.assertEqual(recipients, {self.bob.pk, self.charlie.pk})
        self.assertEqual(notices.first().action_url, reverse('connections:conversations_list') + f'?open_group={conversation.pk}')
        self.client.force_login(self.bob)
        response = self.client.get(reverse('connections:group_chat_detail', args=[conversation.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='new_message', is_read=False).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.charlie, notification_type='new_message', is_read=False).count(), 1)

    def test_notification_preferences_respected(self):
        NotificationPreference.objects.create(user=self.bob, app_messages=False, app_connections=False)
        conversation = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        DirectMessage.objects.create(conversation=conversation, sender=self.alice, content='Hello')
        self.assertFalse(Notification.objects.filter(recipient=self.bob).exists())
        self.client.force_login(self.alice)
        self.assertTrue(self.client.post(reverse('connections:send_request', args=[self.bob.pk])).json()['success'])
        self.assertFalse(Notification.objects.filter(recipient=self.bob).exists())
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse('connections:activity_summary')).json()['pending_requests'], 1)

    def test_activity_endpoint_requires_login_and_disables_cache(self):
        url = reverse('connections:activity_summary')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.charlie)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response.get('Cache-Control', ''))
        self.assertEqual(response.json()['notifications'], [])
        Notification.create_notification(recipient=self.bob, sender=self.alice,
            notification_type='system', title='Private alert', message='Only Bob',
            action_url=reverse('core:all_notifications'))
        self.assertEqual(self.client.get(url).json()['notifications'], [])

    def test_messages_appear_in_messages_badge_only_not_bell_or_general_list(self):
        conversation = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        DirectMessage.objects.create(conversation=conversation, sender=self.alice, content='Private chat text')
        self.client.force_login(self.bob)
        summary = self.client.get(reverse('connections:activity_summary')).json()
        self.assertEqual(summary['unread_messages'], 1)
        self.assertEqual(summary['unread_notifications'], 0)
        self.assertEqual(summary['notifications'], [])
        listing = self.client.get(reverse('core:get_notifications')).json()
        self.assertEqual(listing['notifications'], [])
        self.assertEqual(listing['unread_count'], 0)
        self.assertEqual(self.client.get(reverse('core:get_unread_count')).json()['unread_count'], 0)
        html = self.client.get(reverse('core:all_notifications')).content.decode('utf-8')
        self.assertNotIn('Private chat text', html)
        self.assertNotIn('New message', html)

    def test_request_page_uses_actions_without_browser_confirm(self):
        request = Connection.objects.create(requester=self.alice, receiver=self.bob, status='PENDING')
        self.client.force_login(self.bob)
        response = self.client.get(reverse('connections:connection_requests'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('data-request-action="accept"', html)
        self.assertIn('data-request-action="reject"', html)
        self.assertIn('data-request-grid="incoming"', html)
        self.assertIn('class="request-entry"', html)
        self.assertIn('class="request-entry-actions request-actions"', html)
        self.assertNotIn('class="col-md-6 col-xl-4 mb-3"', html)
        self.assertIn('connection-requests.js', html)
        self.assertNotIn("confirm('Are you sure", html)
        self.client.force_login(self.alice)
        sent = self.client.get(reverse('connections:connection_requests')).content.decode('utf-8')
        self.assertIn('data-request-action="cancel"', sent)
        self.assertIn('data-request-grid="outgoing"', sent)
        self.assertIn('> Withdraw', sent)
        self.assertIn(str(request.pk), sent)
