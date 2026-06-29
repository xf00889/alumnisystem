from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from connections.models import Connection

from .models import Alumni


@override_settings(MIDDLEWARE=[
    middleware for middleware in settings.MIDDLEWARE
    if middleware != 'setup.middleware.SetupRequiredMiddleware'
])
class AlumniDirectoryPrivacyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.viewer = User.objects.create_user('viewer', 'viewer@example.com', 'pass')
        self.owner = User.objects.create_user(
            'owner',
            'owner@example.com',
            'pass',
            first_name='Private',
            last_name='Alumni',
        )
        self.viewer.profile.has_completed_registration = True
        self.viewer.profile.save()
        self.owner.profile.has_completed_registration = True
        self.owner.profile.save()
        self.alumni = Alumni.objects.create(
            user=self.owner,
            college='CAS',
            campus='MAIN',
            graduation_year=2026,
            course='BSINT',
            gender='M',
            province='Negros Oriental',
            city='Dumaguete',
            address='Private Street',
        )

    def test_regular_user_sees_only_limited_alumni_info_even_when_connected(self):
        Connection.objects.create(
            requester=self.viewer,
            receiver=self.owner,
            status='ACCEPTED',
        )
        self.client.force_login(self.viewer)

        list_response = self.client.get(reverse('alumni_directory:alumni_list'), {'search': 'Private'})
        self.assertContains(list_response, 'Private Alumni')
        self.assertNotContains(list_response, 'owner')
        self.assertNotContains(list_response, 'Private Street')

        detail_response = self.client.get(reverse('alumni_directory:alumni_detail', args=[self.alumni.id]))
        self.assertContains(detail_response, 'Private Alumni')
        self.assertContains(detail_response, 'Message')
        self.assertNotContains(detail_response, 'BSINT')
        self.assertNotContains(detail_response, 'Private Street')
        self.assertNotContains(detail_response, 'owner@example.com')
