"""Source-level checks for the unified public sign-in/registration screen."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class UnifiedAuthExperienceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.login = (ROOT / 'templates/account/login.html').read_text(encoding='utf-8')
        cls.css = (ROOT / 'static/css/auth-unified.css').read_text(encoding='utf-8')

    def test_single_page_keeps_both_backend_forms_and_csrf(self):
        self.assertIn('id="loginFormElement"', self.login)
        self.assertIn('id="signupFormElement"', self.login)
        self.assertIn("action=\"{% url 'account_login' %}\"", self.login)
        self.assertIn("action=\"{% url 'accounts:enhanced_signup' %}\"", self.login)
        self.assertGreaterEqual(self.login.count('{% csrf_token %}'), 2)

    def test_new_asset_loaded_only_on_unified_page(self):
        self.assertIn("{% static 'css/auth-unified.css' %}", self.login)
        self.assertTrue(self.css.startswith('/* NORSU unified'))
        self.assertIn('body.auth-public--login', self.css)

    def test_tabs_and_panels_are_accessible_and_dynamic(self):
        self.assertIn('role="tablist"', self.login)
        self.assertIn('role="tabpanel"', self.login)
        self.assertIn('aria-selected', self.login)
        self.assertIn('Your next chapter starts here.', self.login)
        self.assertIn('ArrowLeft', self.login)
        self.assertIn('ArrowRight', self.login)
        self.assertIn('switchTab(\'signup\')', self.login)

    def test_auth_related_features_remain(self):
        for token in (
            'name="remember"',
            'loginPassword',
            'signupPassword1',
            'signupPassword2',
            'validatePassword(password)',
            'g-recaptcha-response',
            "'google' in enabled_sso_providers",
            "{% url 'account_reset_password' %}",
            "{% url 'core:contact_us' %}",
            'legal_terms_page',
            'legal_privacy_page',
        ):
            self.assertIn(token, self.login)

    def test_mobile_style_and_reduced_motion_available(self):
        self.assertIn('@media (max-width: 850px)', self.css)
        self.assertIn('@media (max-width: 520px)', self.css)
        self.assertIn('@media (prefers-reduced-motion: reduce)', self.css)


if __name__ == '__main__':
    unittest.main()
