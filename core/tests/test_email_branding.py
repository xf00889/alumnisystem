"""Run in Django environment: python manage.py test tests.test_email_branding_django"""
from django.test import SimpleTestCase
from django.template.loader import render_to_string
from core.email_branding import brand_transactional_email


class BrandedEmailDjangoTests(SimpleTestCase):
    def test_password_link_preserved_and_branded(self):
        url = 'https://www.norsualumni.com/accounts/security/password-recovery/token/'
        html = brand_transactional_email('Password recovery', 'Use this link: '+url)
        self.assertIn('logo_norsu.png', html)
        self.assertIn('alumni_logo.png', html)
        self.assertIn(url, html)
        self.assertEqual(html.count('<html'), 1)

    def test_untrusted_plain_text_is_escaped(self):
        html = brand_transactional_email('Security alert', '<script>alert(1)</script>')
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_existing_branded_html_is_not_double_wrapped(self):
        html = render_to_string('emails/email_verification.html', {
            'verification_code': '123456', 'user_first_name':'Test'
        })
        self.assertEqual(brand_transactional_email('Test','Test',html),html)
        self.assertEqual(html.count('<html'),1)
        self.assertIn('123456',html)

    def test_conditional_donation_outcome(self):
        html = render_to_string('emails/donation_status_update.html', {
            'donor_name':'Test', 'campaign_name':'Test Fund', 'amount':100,
            'status':'disputed','status_display':'Disputed',
            'reference_number':'REF-100',
        })
        self.assertIn('under review',html)
        self.assertIn('REF-100',html)
