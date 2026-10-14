"""Focused safety checks for the recovery flow's reCAPTCHA v3 contract."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from accounts.forms import PasswordResetEmailForm, PasswordResetNewPasswordForm, PasswordResetOTPForm


class PasswordRecoveryVerificationTests(SimpleTestCase):
    def _form(self, cls, *, token='test-token', result=None, version='v3'):
        config = SimpleNamespace(
            version=version,
            enabled=True,
            verify_token=Mock(return_value=result or {'success': True, 'action': 'password_reset'}),
        )
        if cls is PasswordResetEmailForm:
            values = {'email': 'alumni@example.com'}
        elif cls is PasswordResetOTPForm:
            values = {'email': 'alumni@example.com', 'verification_code': '123456'}
        else:
            values = {'new_password1': 'StrongPassword123!', 'new_password2': 'StrongPassword123!'}
        if token is not None:
            values['captcha'] = token
        with patch('accounts.forms.is_recaptcha_enabled', return_value=True), \
             patch('accounts.forms.get_recaptcha_config', return_value=config), \
             patch('core.recaptcha_widgets.get_recaptcha_public_key', return_value='valid-v3-site-key'), \
             patch('core.recaptcha_widgets.is_recaptcha_enabled', return_value=True):
            form = cls(data=values)
            valid = form.is_valid()
        return form, valid, config

    def test_missing_token_rejected_on_all_three_steps(self):
        for form_class in (PasswordResetEmailForm, PasswordResetOTPForm, PasswordResetNewPasswordForm):
            with self.subTest(form_class=form_class.__name__):
                form, valid, config = self._form(form_class, token=None)
                self.assertFalse(valid)
                self.assertIn('captcha', form.errors)
                config.verify_token.assert_not_called()

    def test_valid_v3_token_accepted_and_verified_once(self):
        form, valid, config = self._form(PasswordResetEmailForm)
        self.assertTrue(valid, form.errors)
        config.verify_token.assert_called_once_with('test-token')

    def test_wrong_action_rejected(self):
        form, valid, _ = self._form(PasswordResetEmailForm, result={'success': True, 'action': 'login'})
        self.assertFalse(valid)
        self.assertIn('captcha', form.errors)

    def test_failed_verification_rejected(self):
        form, valid, _ = self._form(PasswordResetEmailForm, result={'success': False, 'action': 'password_reset'})
        self.assertFalse(valid)
        self.assertIn('captcha', form.errors)

    def test_v2_key_configuration_cannot_silently_bypass_v3(self):
        form, valid, config = self._form(PasswordResetEmailForm, version='v2')
        self.assertFalse(valid)
        config.verify_token.assert_not_called()

    def test_captcha_absent_when_disabled(self):
        with patch('accounts.forms.is_recaptcha_enabled', return_value=False):
            form = PasswordResetEmailForm()
        self.assertNotIn('captcha', form.fields)
