"""Offline source checks, no live outbound messages or database access."""
import pathlib
import re
import unittest

PATCH = pathlib.Path(__file__).resolve().parents[1]

class BrandedEmailSourceChecks(unittest.TestCase):
    def test_two_real_logo_paths(self):
        html = (PATCH/'templates/emails/base_transactional.html').read_text()
        for name in ('logo_norsu.png','alumni_logo.png'):
            self.assertIn(name, html)
        self.assertIn('Office of Alumni Affairs',html)
        self.assertIn('data-norsu-email="transactional"',html)
        self.assertIn('max-width:600px',html)
        self.assertIn('role="presentation"',html)
        self.assertIn('alt="NORSU seal"',html)
    def test_all_known_html_templates_use_base(self):
        for path in list((PATCH/'templates/emails').glob('*.html'))+list((PATCH/'templates/announcements/email').glob('*.html')):
            if path.name == 'base_transactional.html': continue
            with self.subTest(path=path.name):
                self.assertIn("{% extends 'emails/base_transactional.html' %}",path.read_text())
    def test_no_placeholder_navigation(self):
        for p in (PATCH/'templates').rglob('*.html'):
            self.assertNotIn('href="#"',p.read_text(),p.name)
    def test_donation_proof_not_a_receipt(self):
        self.assertIn('does not confirm receipt of funds',(PATCH/'templates/emails/donation_confirmation.html').read_text())
    def test_plain_only_goes_through_branded_gateway(self):
        self.assertIn('brand_transactional_email(subject, message, html_message)',(PATCH/'core/email_utils.py').read_text())
        self.assertIn('autoescape=True',(PATCH/'core/email_branding.py').read_text())
        self.assertIn('email_body_html|safe',(PATCH/'templates/emails/plain_message.html').read_text())
    def test_feedback_mail_on_change_not_notes(self):
        text=(PATCH/'feedback/signals.py').read_text()
        self.assertIn('transaction.on_commit(send_notice)',text)
        self.assertIn('old_status == instance.status',text)
        self.assertNotIn('instance.admin_notes',text)
    def test_donation_guest_goes_to_provider(self):
        s=(PATCH/'donations/payment_flow.py').read_text()
        self.assertIn('send_email_with_provider(',s)
        self.assertNotIn('send_mail(',s)
    def test_announcement_brevo_not_blocked_by_smtp_probe(self):
        s=(PATCH/'announcements/utils.py').read_text()
        self.assertNotIn('socket.create_connection',s)
        self.assertNotIn('get_connection(',s)
    def test_balance_django_blocks(self):
        patterns={
            'block': (r'\{%\s*block\s+\w+\s*%\}',r'\{%\s*endblock\s*%\}'),
            'if':(r'\{%\s*if\s+[^%]+%\}',r'\{%\s*endif\s*%\}')
        }
        for p in (PATCH/'templates').rglob('*.html'):
            t=p.read_text()
            for name,(opening,closing) in patterns.items():
                with self.subTest(path=p.name,tag=name):
                    self.assertEqual(len(re.findall(opening,t)),len(re.findall(closing,t)))
    def test_context_contracts_are_preserved(self):
        req={
          'email_verification.html':['verification_code','user_first_name'],
          'resend_verification.html':['verification_code'],
          'password_reset_verification.html':['verification_code'],
          'donation_confirmation.html':['reference_number','status_display','campaign_name','donor_name'],
          'donation_status_update.html':['status','status_display','amount','reference_number'],
          'donation_receipt.html':['reference_number','amount','campaign_name'],
          'role_assigned.html':['role_name','site_url'],
          'role_removed.html':['role_name','site_url'],
          'user_created.html':['user.email','password','site_url'],
        }
        for name,fields in req.items():
            template=(PATCH/'templates/emails'/name).read_text()
            for key in fields:
                with self.subTest(file=name,field=key): self.assertIn(key,template)

if __name__=='__main__': unittest.main()
