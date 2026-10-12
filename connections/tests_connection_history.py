"""History must remain readable to its participants after a connection is removed.

Removal revokes permission to send, not permission to read already-shared direct messages.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from setup.models import SetupState
from .models import Connection, DirectConversation, DirectMessage


class FormerConnectionHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.alice = User.objects.create_user(username='former_alice', password='test-pass')
        cls.bob = User.objects.create_user(username='former_bob', password='test-pass')
        cls.outsider = User.objects.create_user(username='former_stranger', password='test-pass')
        cls.connection = Connection.objects.create(requester=cls.alice, receiver=cls.bob, status='ACCEPTED')
        cls.conversation = DirectConversation.get_or_create_conversation(cls.alice, cls.bob)
        cls.message = DirectMessage.objects.create(conversation=cls.conversation, sender=cls.alice, content='Previously shared history')

    def detail(self, user):
        return reverse('connections:direct_messages', args=[user.pk])

    def test_former_participants_can_read_history_but_no_composer(self):
        self.connection.delete()
        self.client.force_login(self.alice)
        response = self.client.get(self.detail(self.bob), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Previously shared history')
        self.assertContains(response, 'must reconnect to send', status_code=200)
        self.assertNotContains(response, 'id="messageForm"')
        self.client.force_login(self.bob)
        response = self.client.get(self.detail(self.alice), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Previously shared history')

    def test_sending_is_blocked_after_connection_removal(self):
        self.connection.delete()
        self.client.force_login(self.alice)
        original_count = DirectMessage.objects.count()
        response = self.client.post(self.detail(self.bob), {'content': 'Must not send'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])
        second = self.client.post(reverse('connections:send_message', args=[self.bob.pk]), {'content': 'Also must not send'})
        self.assertEqual(second.status_code, 403)
        self.assertFalse(second.json()['success'])
        self.assertEqual(DirectMessage.objects.count(), original_count)

    def test_read_only_notice_links_to_alumni_profile(self):
        from alumni_directory.models import Alumni
        alumni, _ = Alumni.objects.get_or_create(
            user=self.bob, defaults={
                'graduation_year': 2020, 'college': 'CAS', 'campus': 'MAIN',
                'course': 'BSIT', 'gender': 'O', 'province': 'Negros Oriental',
                'city': 'Dumaguete', 'address': '',
            },
        )
        self.connection.delete()
        self.client.force_login(self.alice)
        response = self.client.get(self.detail(self.bob), HTTP_HX_REQUEST='true')
        self.assertContains(response, 'data-conversation-read-only="true"')
        self.assertContains(response, reverse('alumni_directory:alumni_detail', args=[alumni.pk]))
        self.assertNotContains(response, 'id="messageForm"')

    def test_former_contact_sending_returns_quiet_forbidden_response(self):
        self.connection.delete()
        self.client.force_login(self.alice)
        response = self.client.post(reverse('connections:send_message', args=[self.bob.pk]), {'content': 'Not allowed'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'conversation_read_only')
        self.assertTrue(response.json()['silent'])
        self.assertEqual(DirectMessage.objects.count(), 1)

    def test_strangers_cannot_read_history_or_create_new_conversation(self):
        self.connection.delete()
        self.client.force_login(self.outsider)
        response = self.client.get(self.detail(self.bob), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('Previously shared history', response.content.decode())
        self.client.force_login(self.alice)
        response = self.client.get(self.detail(self.outsider), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DirectConversation.objects.count(), 1)

    def test_blocked_user_cannot_read_old_conversation(self):
        self.connection.status = 'BLOCKED'
        self.connection.save(update_fields=['status'])
        self.client.force_login(self.alice)
        response = self.client.get(self.detail(self.bob), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 403)

    def test_reconnected_users_can_send_again(self):
        self.connection.delete()
        Connection.objects.create(requester=self.bob, receiver=self.alice, status='ACCEPTED')
        self.client.force_login(self.alice)
        response = self.client.get(self.detail(self.bob), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="messageForm"')
