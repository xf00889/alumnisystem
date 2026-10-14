"""Regression tests for profile name ordering and password-recovery CSRF policy."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.middleware.csrf import CsrfViewMiddleware
from django.test.utils import override_settings
from unittest.mock import patch
from allauth.account.models import EmailAddress


class ProfileAndRecoveryRegressionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='profile-order-test@example.com',
            email='profile-order-test@example.com',
            password='StrongTestPassword!123',
            first_name='Alex', last_name='Santos', is_active=True,
        )
        EmailAddress.objects.create(user=self.user, email=self.user.email, primary=True, verified=True)
        profile = self.user.profile
        profile.middle_name = 'Cruz'
        profile.maiden_name = 'Reyes'
        profile.save(update_fields=['middle_name','maiden_name'])

    def test_name_fields_are_ordered_in_editor(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:edit_profile'))
        self.assertEqual(response.status_code,200)
        content=response.content.decode()
        names=[content.index('name="'+field+'"') for field in ('first_name','middle_name','last_name','maiden_name')]
        self.assertEqual(names,sorted(names))

    def test_profile_name_order_and_owner_only_name_history(self):
        self.client.force_login(self.user)
        response=self.client.get(reverse('accounts:profile_detail'))
        self.assertEqual(response.status_code,200)
        html=response.content.decode()
        markers=[html.index('>First Name</span>'),html.index('>Middle Name</span>'),html.index('>Last Name</span>'),html.index('>Maiden Name (if applicable)</span>')]
        self.assertEqual(markers,sorted(markers))
        other=get_user_model().objects.create_user(username='another-profile-test',email='another-profile-test@example.com',password='SafePassword!123')
        other.profile.middle_name='PrivateMiddle'
        other.profile.maiden_name='PrivateMaiden'
        other.profile.save()
        response=self.client.get(reverse('accounts:profile_detail',kwargs={'username':other.username}))
        self.assertNotContains(response,'PrivateMaiden')
        self.assertNotContains(response,'PrivateMiddle')

    @patch('accounts.alumni_password_views.send_email_with_provider', return_value=True)
    def test_password_recovery_post_accepts_normal_same_origin_csrf(self, sender):
        browser=Client(enforce_csrf_checks=True)
        browser.force_login(self.user)
        url=reverse('accounts:password_recovery_request')
        response=browser.get(url)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('content="no-referrer"',response.content.decode())
        cookie=browser.cookies.get(settings.CSRF_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        from django.middleware.csrf import _mask_cipher_secret
        token=_mask_cipher_secret(cookie.value)
        response=browser.post(url,{'email':self.user.email,'csrfmiddlewaretoken':token},HTTP_ORIGIN='https://norsualumni.com',HTTP_HOST='norsualumni.com',secure=True)
        self.assertEqual(response.status_code,302)
        self.assertTrue(sender.called)
