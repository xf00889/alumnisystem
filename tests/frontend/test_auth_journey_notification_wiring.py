"""Source-level coverage for the auth journey and global report notifications.

Run with: python -m unittest discover -s tests/frontend -p 'test_auth_journey_notification_wiring.py' -v
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AuthJourneyNotificationWiringTests(unittest.TestCase):
    def test_journey_screen_styles_are_loaded(self):
        paths = [
            'templates/accounts/verify_email.html',
            'templates/accounts/password_reset_email.html',
            'templates/accounts/password_reset_otp.html',
            'templates/accounts/password_reset_new_password.html',
            'templates/accounts/post_registration.html',
            'templates/account/password_reset.html',
        ]
        for path in paths:
            with self.subTest(path=path):
                t = (ROOT / path).read_text()
                self.assertIn("{% static 'css/auth-journey.css' %}", t)
                self.assertIn('auth-public--journey', t)
                self.assertIn('components/university_header.html', t)

    def test_signup_verification_preserves_csrf_and_code(self):
        t = (ROOT / 'templates/accounts/verify_email.html').read_text()
        self.assertIn('name="email"', t)
        self.assertIn('form.verification_code', t)
        self.assertIn('{% csrf_token %}', t)
        self.assertIn('id="resendBtn"', t)

    def test_reset_flows_preserve_endpoints(self):
        for template, endpoint in [
            ('password_reset_email.html', "{% url 'accounts:password_reset_email' %}"),
            ('password_reset_otp.html', "{% url 'accounts:password_reset_otp' %}"),
            ('password_reset_new_password.html', "{% url 'accounts:password_reset_new_password' %}"),
        ]:
            t = (ROOT / 'templates/accounts' / template).read_text()
            self.assertIn(endpoint, t)
            self.assertIn('{% csrf_token %}', t)

    def test_post_registration_preserves_form_actions(self):
        t = (ROOT / 'templates/accounts/post_registration.html').read_text()
        self.assertIn('id="postRegForm"', t)
        self.assertIn('{{ form|crispy }}', t)
        self.assertIn('id="cancelRegForm"', t)
        self.assertIn('id="duplicateCheckBanner"', t)

    def test_notification_goes_to_existing_global_inbox(self):
        t = (ROOT / 'alumni_groups/community_views.py').read_text()
        self.assertIn('from core.models.notifications import Notification', t)
        self.assertIn("notification_type='system'", t)
        self.assertIn("reverse('core:all_notifications')", t)
        self.assertIn('select_for_update()', t)
        self.assertIn("if report.status != 'OPEN'", t)

    def test_scoped_css(self):
        t = (ROOT / 'static/css/auth-journey.css').read_text()
        self.assertIn('body.auth-public--journey', t)
        self.assertIn('@media (max-width:520px)', t)
        self.assertIn('prefers-reduced-motion', t)


if __name__ == '__main__':
    unittest.main()
