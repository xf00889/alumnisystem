"""Catch inbox regressions that only appear with message records in the DB."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import DirectConversation, DirectMessage


class ConversationInboxReadinessTests(TestCase):
    def test_get_conversations_with_message_records(self):
        User = get_user_model()
        member = User.objects.create_user(username='inbox_member', password='test-password')
        peer = User.objects.create_user(username='inbox_peer', password='test-password')
        conversation = DirectConversation.objects.create(conversation_type='direct')
        conversation.participants.add(member, peer)
        DirectMessage.objects.create(conversation=conversation, sender=peer, content='Hello')
        self.client.force_login(member)
        response = self.client.get(reverse('connections:conversations_list'))
        self.assertEqual(response.status_code, 200)
