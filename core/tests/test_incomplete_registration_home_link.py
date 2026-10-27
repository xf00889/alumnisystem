"""An incomplete alumni can browse the public home without cancelling registration."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

TEST_MIDDLEWARE = [m for m in settings.MIDDLEWARE
                   if m != 'setup.middleware.SetupRequiredMiddleware']


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class IncompleteRegistrationHomeLinkTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'incomplete-home-test', 'incomplete-home@example.com', 'StrongPass123!'
        )
        self.client.force_login(self.user)

    def test_normal_home_still_requires_completed_registration(self):
        response = self.client.get(reverse('core:home'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:post_registration'))

    def test_back_home_shows_public_landing_without_deleting_user(self):
        response = self.client.get(reverse('core:home') + '?view=public', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.has_completed_registration)

    def test_registration_form_links_to_read_only_public_home(self):
        response = self.client.get(reverse('accounts:post_registration'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('core:home') + '?view=public')
