"""Restricted HR bypasses alumni-only post-registration without being marked alumni."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.adapters import CustomAccountAdapter, CustomSocialAccountAdapter
from jobs.hr_access import is_hr_only


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class HRPostRegistrationBypassTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        cls.addClassCleanup(setup_guard.stop)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.hr = User.objects.create_user(
            username='onboarding_hr', email='onboarding-hr@example.org',
            password='StrongHRPass!2026', is_active=True,
        )
        cls.hr.profile.is_hr = True
        cls.hr.profile.save(update_fields=['is_hr'])
        cls.alumni = User.objects.create_user(
            username='onboarding_alumnus', email='onboarding-alumni@example.org',
            password='StrongAlumniPass!2026', is_active=True,
        )

    def test_hr_redirects_to_dashboard_after_password_or_social_login(self):
        request = RequestFactory().get('/accounts/login/', secure=True)
        request.user = self.hr
        self.assertTrue(is_hr_only(self.hr))
        self.assertFalse(self.hr.profile.has_completed_registration)
        self.assertEqual(
            CustomAccountAdapter().get_login_redirect_url(request),
            reverse('jobs:hr_dashboard'),
        )
        social = CustomSocialAccountAdapter()
        self.assertEqual(social.get_login_redirect_url(request), reverse('jobs:hr_dashboard'))
        self.assertEqual(social.get_signup_redirect_url(request), reverse('jobs:hr_dashboard'))

    def test_hr_direct_get_and_post_never_enter_alumni_setup(self):
        self.client.force_login(self.hr)
        url = reverse('accounts:post_registration')
        for response in (self.client.get(url, secure=True), self.client.post(url, {}, secure=True)):
            self.assertRedirects(
                response, reverse('jobs:hr_dashboard'), fetch_redirect_response=False
            )
        self.hr.profile.refresh_from_db()
        self.assertFalse(self.hr.profile.has_completed_registration)

    def test_hr_cannot_cancel_and_delete_admin_provisioned_account(self):
        self.client.force_login(self.hr)
        self.assertRedirects(
            self.client.post(reverse('accounts:cancel_registration'), secure=True),
            reverse('jobs:hr_dashboard'), fetch_redirect_response=False
        )
        self.assertTrue(get_user_model().objects.filter(pk=self.hr.pk).exists())

    def test_incomplete_regular_alumnus_still_uses_alumni_registration(self):
        request = RequestFactory().get('/accounts/login/', secure=True)
        request.user = self.alumni
        self.assertFalse(is_hr_only(self.alumni))
        self.assertEqual(
            CustomAccountAdapter().get_login_redirect_url(request),
            reverse('accounts:post_registration'),
        )
        self.assertEqual(
            CustomSocialAccountAdapter().get_login_redirect_url(request),
            reverse('accounts:post_registration'),
        )
        self.client.force_login(self.alumni)
        response = self.client.get(reverse('accounts:post_registration'), secure=True)
        self.assertEqual(response.status_code, 200)

    def test_hr_home_redirects_to_hr_workspace(self):
        self.client.force_login(self.hr)
        self.assertRedirects(
            self.client.get(reverse('core:home'), secure=True),
            reverse('jobs:hr_dashboard'), fetch_redirect_response=False,
        )
