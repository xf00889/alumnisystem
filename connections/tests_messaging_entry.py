"""Regression coverage for profile -> Messages deep links.

The inbox must select the requested person only if the users are connected,
and may create an empty direct conversation without an initial message.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from setup.models import SetupState
from .models import Connection, DirectConversation, DirectMessage


class ProfileMessagingEntryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.alice = User.objects.create_user(username='inbox_alice', password='test-password')
        cls.bob = User.objects.create_user(username='inbox_bob', password='test-password')
        cls.stranger = User.objects.create_user(username='inbox_stranger', password='test-password')
        cls.connection = Connection.objects.create(
            requester=cls.alice, receiver=cls.bob, status='ACCEPTED'
        )

    def setUp(self):
        self.client.force_login(self.alice)

    def test_connected_alumnus_opens_empty_direct_conversation(self):
        response = self.client.get(reverse('connections:conversations_list'), {'with': self.bob.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_conversation_user_id'], self.bob.pk)
        self.assertContains(response, f'data-initial-chat-user-id="{self.bob.pk}"')
        self.assertContains(response, f'data-direct-user-id="{self.bob.pk}"')
        conversation = DirectConversation.objects.get(conversation_type='direct')
        self.assertEqual(conversation.participants.count(), 2)
        self.assertEqual(DirectMessage.objects.count(), 0)

    def test_existing_conversation_is_selected_not_duplicated(self):
        conversation = DirectConversation.get_or_create_conversation(self.alice, self.bob)
        response = self.client.get(reverse('connections:conversations_list'), {'with': self.bob.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_conversation_user_id'], self.bob.pk)
        self.assertEqual(DirectConversation.objects.filter(conversation_type='direct').count(), 1)
        self.assertTrue(DirectConversation.objects.filter(pk=conversation.pk).exists())

    def test_unconnected_user_cannot_create_a_conversation(self):
        response = self.client.get(reverse('connections:conversations_list'), {'with': self.stranger.pk})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(DirectConversation.objects.exists())

    def test_former_connection_cannot_create_a_new_conversation(self):
        self.connection.delete()
        response = self.client.get(reverse('connections:conversations_list'), {'with': self.bob.pk})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(DirectConversation.objects.exists())

    def test_inbox_without_target_still_renders_normally(self):
        response = self.client.get(reverse('connections:conversations_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['selected_conversation_user_id'])
