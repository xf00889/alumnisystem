"""Regression tests for recipient personalization across university emails.

Tests render the final HTML; a template parsing successfully does not mean
that all personalization placeholders were actually interpolated.
"""
from datetime import datetime
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from accounts.email_utils import (
    render_password_reset_email,
    render_resend_verification_email,
    render_verification_email,
)


class EmailTemplateRenderingTests(SimpleTestCase):
    def setUp(self):
        self.user = SimpleNamespace(
            first_name='Maria',
            last_name='Santos',
            email='maria@example.invalid',
            get_full_name=lambda: 'Maria Santos',
        )

    def assert_rendered_not_template_source(self, html):
        """Catch template syntax mistakenly emitted to the recipient."""
        self.assertNotIn('{{', html)
        self.assertNotIn('{%', html)
        self.assertNotIn("{'{", html)
        self.assertNotIn('Hello ,', html)
        self.assertNotIn('Hello  ,', html)
        self.assertEqual(html.count('<html'), 1)

    def test_verification_greeting_is_personalized(self):
        html = render_verification_email(self.user, '123456')
        self.assertIn('Hello Maria,', html)
        self.assertIn('123456', html)
        self.assert_rendered_not_template_source(html)

    def test_resend_and_password_recovery_greetings(self):
        for renderer in (render_resend_verification_email, render_password_reset_email):
            with self.subTest(renderer=renderer.__name__):
                html = renderer(self.user, '123456')
                self.assertIn('Hello Maria,', html)
                self.assertIn('123456', html)
                self.assert_rendered_not_template_source(html)

    def test_missing_first_name_uses_neutral_greeting(self):
        self.user.first_name = '  '
        for renderer in (render_verification_email, render_resend_verification_email, render_password_reset_email):
            with self.subTest(renderer=renderer.__name__):
                html = renderer(self.user, '123456')
                self.assertIn('Hello Alumni member,', html)
                self.assert_rendered_not_template_source(html)

    def test_all_existing_transactional_templates_render_without_placeholders(self):
        context = {
            'user': self.user,
            'user_first_name': 'Maria',
            'verification_code': '123456',
            'expiry_minutes': 15,
            'donor_name': 'Maria Santos',
            'amount': 100,
            'reference_number': 'QA-123',
            'campaign_name': 'Scholarship Fund',
            'donation_date': datetime(2026, 10, 14, 9, 0),
            'verification_date': datetime(2026, 10, 15, 9, 0),
            'status': 'disputed',
            'status_display': 'Disputed',
            'feedback_subject': 'Sample',
            'feedback_id': 123,
            'recipient_name': 'Maria Santos',
            'new_status': 'In progress',
            'role_name': 'mentor',
            'site_url': 'https://www.norsualumni.com/',
            'is_active': True,
            'email_subject': 'Sample notification',
            'email_body_html': 'Hello Maria Santos',
            'password': None,
        }
        templates = (
            'donation_confirmation.html',
            'donation_receipt.html',
            'donation_status_update.html',
            'email_verification.html',
            'feedback_status_update.html',
            'mentor_reactivation_verification.html',
            'password_reset_verification.html',
            'plain_message.html',
            'resend_verification.html',
            'role_assigned.html',
            'role_removed.html',
            'status_changed.html',
            'user_created.html',
        )
        for name in templates:
            with self.subTest(template=name):
                html = render_to_string('emails/' + name, context)
                self.assert_rendered_not_template_source(html)
                self.assertIn('Negros Oriental State University', html)
