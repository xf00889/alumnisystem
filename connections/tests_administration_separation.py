"""Admin staff must not be able to use alumni social actions via forged requests."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Connection


class AdministrationSocialPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user(username='admin_social_staff', password='test', is_staff=True)
        cls.alumni = User.objects.create_user(username='admin_social_alumni', password='test')

    def test_admin_cannot_send_requests_or_messages(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('connections:send_request', kwargs={'user_id': self.alumni.pk})).status_code, 403)
        self.assertEqual(self.client.post(reverse('connections:send_message', kwargs={'user_id': self.alumni.pk}), {'content':'Hello'}).status_code, 403)
        self.assertEqual(self.client.get(reverse('connections:conversations_list')).status_code, 403)
        self.assertFalse(Connection.objects.exists())

    def test_alumni_cannot_invite_admin(self):
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(reverse('connections:send_request', kwargs={'user_id': self.staff.pk})).status_code, 403)
        self.assertFalse(Connection.objects.exists())
