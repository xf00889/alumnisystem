"""Regression tests for unified inbox links and legacy message URLs."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Connection


@override_settings(SECURE_SSL_REDIRECT=False)
class UnifiedMessageRoutingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user(username='nav_alice', password='testpass')
        cls.bob = User.objects.create_user(username='nav_bob', password='testpass')
        Connection.objects.create(requester=cls.alice, receiver=cls.bob, status='ACCEPTED')

    def test_direct_full_page_routes_to_unified_inbox(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('connections:direct_messages', args=[self.bob.pk]), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('connections:conversations_list') + f'?with={self.bob.pk}')

    def test_htmx_detail_route_remains_available(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse('connections:direct_messages', args=[self.bob.pk]),
                                   HTTP_HX_REQUEST='true', secure=True)
        self.assertEqual(response.status_code, 200)
