"""Recipient-scoped unread thread counters for the alumni navigation."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Notification
from setup.models import SetupState
from .models import Connection, DirectConversation, DirectMessage


@override_settings(SECURE_SSL_REDIRECT=False)
class MessageUnreadBadgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.alice = User.objects.create_user(username='badge_alice', password='testing-pass-123')
        cls.bob = User.objects.create_user(username='badge_bob', password='testing-pass-123')
        cls.charlie = User.objects.create_user(username='badge_charlie', password='testing-pass-123')
        Connection.objects.create(requester=cls.alice, receiver=cls.bob, status='ACCEPTED')
        Connection.objects.create(requester=cls.charlie, receiver=cls.bob, status='ACCEPTED')

    def count(self):
        response = self.client.get(reverse('connections:activity_summary'))
        self.assertEqual(response.status_code, 200)
        return response.json()['unread_messages']

    def test_two_unread_messages_in_one_thread_count_once_then_clear(self):
        thread = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        DirectMessage.objects.create(conversation=thread, sender=self.alice, content='First')
        DirectMessage.objects.create(conversation=thread, sender=self.alice, content='Second')
        self.client.force_login(self.bob)
        self.assertEqual(self.count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='new_message', is_read=False).count(), 2)
        reply = self.client.get(reverse('connections:direct_messages', args=[self.alice.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(self.count(), 0)
        self.assertFalse(Notification.objects.filter(recipient=self.bob, notification_type='new_message', is_read=False).exists())
        self.assertFalse(DirectMessage.objects.filter(conversation=thread, is_read=False).exists())

    def test_only_opened_thread_cleared_other_thread_remains(self):
        thread1 = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        thread2 = DirectConversation.get_or_create_conversation(self.charlie, self.bob)
        DirectMessage.objects.create(conversation=thread1, sender=self.alice, content='First')
        DirectMessage.objects.create(conversation=thread2, sender=self.charlie, content='Second')
        self.client.force_login(self.bob)
        self.assertEqual(self.count(), 2)
        self.client.get(reverse('connections:direct_messages', args=[self.alice.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(self.count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.bob, notification_type='new_message', is_read=False).count(), 1)

    def test_inbox_visit_without_opening_thread_does_not_mark_as_read(self):
        thread = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        DirectMessage.objects.create(conversation=thread, sender=self.alice, content='Incoming')
        self.client.force_login(self.bob)
        self.client.get(reverse('connections:conversations_list'))
        self.assertEqual(self.count(), 1)
        self.client.get(reverse('connections:direct_messages', args=[self.alice.pk]))
        # A full-page direct link is redirected to the inbox, not rendered as read.
        self.assertEqual(self.count(), 1)

    def test_group_read_is_per_recipient_and_does_not_clear_others(self):
        thread = DirectConversation.create_group_chat(self.alice, [self.bob, self.charlie], 'Discussion')
        DirectMessage.objects.create(conversation=thread, sender=self.alice, content='Hello group')
        self.client.force_login(self.bob)
        self.assertEqual(self.count(), 1)
        response = self.client.get(reverse('connections:group_chat_detail', args=[thread.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.count(), 0)
        self.client.force_login(self.charlie)
        self.assertEqual(self.count(), 1)
        self.assertEqual(thread.get_unread_count_for_user(self.charlie), 1)

    def test_already_read_direct_message_has_no_stale_nav_badge(self):
        thread = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        message = DirectMessage.objects.create(conversation=thread, sender=self.alice, content='Old')
        DirectMessage.objects.filter(pk=message.pk).update(is_read=True)
        self.client.force_login(self.bob)
        self.assertEqual(self.count(), 0)
        self.client.get(reverse('connections:direct_messages', args=[self.alice.pk]), HTTP_HX_REQUEST='true')
        self.assertFalse(Notification.objects.filter(recipient=self.bob, notification_type='new_message', is_read=False).exists())

    def test_old_unlinked_notification_url_cleared_on_open(self):
        DirectConversation.get_or_create_conversation(self.alice, self.bob)
        old_url = reverse('connections:direct_messages', args=[self.alice.pk])
        Notification.create_notification(
            recipient=self.bob, sender=self.alice, notification_type='new_message',
            title='Old inbox notice', message='Test', action_url=old_url,
        )
        self.client.force_login(self.bob)
        self.assertEqual(self.count(), 1)
        self.client.get(reverse('connections:direct_messages', args=[self.alice.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(self.count(), 0)
        self.assertFalse(Notification.objects.filter(recipient=self.bob, notification_type='new_message', is_read=False).exists())
