"""Donation proof persistence, email preview and fraud regressions.

Run: python manage.py test donations.tests_proof_integrity
"""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .email_utils import send_donation_confirmation_email, send_donation_receipt_email
from .fraud_detection import fraud_detector
from .models import Campaign, CampaignType, Donation, FraudAlert


class ProofIntegrityTests(TestCase):
    def setUp(self):
        # This test database has no first-run setup state. Exercise the donation
        # endpoint rather than the installation wizard; production middleware
        # remains active and unchanged outside this test case.
        setup_check = patch(
            'setup.middleware.SetupRequiredMiddleware._is_setup_complete',
            return_value=True,
        )
        setup_check.start()
        self.addCleanup(setup_check.stop)
        self.user = get_user_model().objects.create_user(
            username='proof-integrity-alumni', password='password12345', email='proof@example.com')
        category = CampaignType.objects.create(name='Proof integrity', slug='proof-integrity')
        self.campaign = Campaign.objects.create(
            name='Proof integrity campaign', slug='proof-integrity-campaign',
            campaign_type=category, description='Test', short_description='Test',
            goal_amount=Decimal('5000.00'), visibility='public', status='active',
            allow_donations=True)
        self.donation = Donation.objects.create(
            donor=self.user, campaign=self.campaign, amount=Decimal('1000.00'),
            status='pending_payment')
        self.client.force_login(self.user)
        self.url = reverse('donations:upload_payment_proof', kwargs={'pk': self.donation.pk})

    def image_file(self):
        output = BytesIO()
        Image.new('RGB', (8, 8), (255, 255, 255)).save(output, format='PNG')
        return SimpleUploadedFile('gcash-proof.png', output.getvalue(), content_type='image/png')

    @patch('donations.fraud_detection.fraud_detector.analyze_donation', return_value=[])
    @patch('donations.signals.send_donation_confirmation_email', return_value=True)
    def test_submission_persists_reference_and_receipt_before_acknowledgement(self, email, fraud):
        try:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(self.url, {
                    'reference_number': 'GCASH-PROOF-999888',
                    'payment_proof': self.image_file(),
                })
            self.assertEqual(response.status_code, 302)
            self.assertNotEqual(response.url, '/setup/')
            self.donation.refresh_from_db()
            self.assertEqual(self.donation.status, 'pending_verification')
            self.assertEqual(self.donation.reference_number, 'GCASH-PROOF-999888')
            self.assertTrue(self.donation.payment_proof.name)
            self.assertTrue(self.donation.payment_proof.storage.exists(self.donation.payment_proof.name))
            email.assert_called_once()
            self.assertEqual(email.call_args.args[0].reference_number, 'GCASH-PROOF-999888')
        finally:
            self.donation.refresh_from_db()
            if self.donation.payment_proof:
                self.donation.payment_proof.delete(save=False)

    def test_missing_reference_cannot_advance_status(self):
        response = self.client.post(self.url, {
            'reference_number': '', 'payment_proof': self.image_file(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'donations/donor_proof.html')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'pending_payment')
        self.assertFalse(self.donation.reference_number)
        self.assertFalse(self.donation.payment_proof)

    @patch('donations.signals.send_donation_confirmation_email')
    def test_old_broken_pending_verification_record_does_not_generate_acknowledgement(self, email):
        with self.captureOnCommitCallbacks(execute=True):
            self.donation.status = 'pending_verification'
            self.donation.save(update_fields=['status'])
        email.assert_not_called()

    @patch('donations.email_utils.send_email_with_provider', return_value=True)
    def test_acknowledgement_requires_persisted_reference_and_proof(self, email):
        self.donation.status = 'pending_verification'
        self.assertFalse(send_donation_confirmation_email(self.donation))
        email.assert_not_called()

    def test_empty_gc_gcash_reference_uses_donation_id_in_fraud_label(self):
        alert = FraudAlert.objects.create(donation=self.donation, alert_type='manual_review',
                                         severity='low', description='Check transaction')
        self.assertIn(f'Donation #{self.donation.pk}', str(alert))
        self.assertNotIn('None', str(alert))

    def test_round_amount_not_automatically_flagged(self):
        self.assertIsNone(fraud_detector.check_suspicious_amount(self.donation))

    def test_unpaid_repeated_intents_do_not_trigger_amount_pattern(self):
        for _ in range(6):
            Donation.objects.create(campaign=self.campaign, amount=Decimal('1000.00'),
                                    status='pending_payment')
        self.assertIsNone(fraud_detector.check_suspicious_amount(self.donation))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    @patch('core.email_utils.send_email_with_smtp_config', return_value=1)
    @patch('core.email_utils.get_active_email_provider', return_value=None)
    @patch('core.email_utils.get_brevo_settings', return_value={})
    def test_console_preview_not_counted_as_real_donation_delivery(self, brevo, provider, smtp):
        from core.email_utils import send_email_with_provider
        result = send_email_with_provider('Test', 'Test', ['test@example.com'],
                                          provider_type='smtp', require_delivery=True)
        self.assertEqual(result, 0)
        smtp.assert_called_once()

