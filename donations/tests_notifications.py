"""Public campaign access, mandatory guest email, and transactional notices.

Run locally: python manage.py test donations.tests_notifications
"""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from PIL import Image

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import DonationForm
from .models import Campaign, CampaignType, Donation


class PublicCampaignAndEmailRequirementsTests(TestCase):
    def setUp(self):
        # The isolated test DB is not through the deployment setup wizard.
        # Keep production installation enforcement intact; bypass only its
        # completion check for these public/alumni page integration tests.
        setup_check = patch(
            'setup.middleware.SetupRequiredMiddleware._is_setup_complete',
            return_value=True,
        )
        setup_check.start()
        self.addCleanup(setup_check.stop)
        category = CampaignType.objects.create(name='Public Giving', slug='public-giving-test')
        common = dict(campaign_type=category, description='Help students',
                      short_description='Help students with scholarships',
                      goal_amount=Decimal('5000'), start_date=timezone.now() - timedelta(days=1),
                      allow_donations=True)
        self.open = Campaign.objects.create(name='Public Open Campaign', slug='public-open-campaign',
                                             visibility='public', status='active', **common)
        Campaign.objects.create(name='Private Campaign', slug='private-campaign',
                                visibility='registered_alumni', status='active', **common)
        Campaign.objects.create(name='Draft Campaign', slug='draft-campaign',
                                visibility='public', status='draft', **common)
        Campaign.objects.create(name='Disabled Campaign', slug='disabled-campaign',
                                visibility='public', status='active',
                                **{**common, 'allow_donations': False})

    def test_guest_browse_redirects_to_public_campaign_directory(self):
        response = self.client.get(reverse('donations:campaign_list') + '?search=Public')
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('donations:public_campaign_list'), response.url)
        self.assertIn('search=Public', response.url)

    def test_guest_directory_uses_public_layout_and_filters_private_campaigns(self):
        response = self.client.get(reverse('donations:public_campaign_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'donations/public_campaign_list.html')
        self.assertContains(response, 'Public Open Campaign')
        for hidden in ('Private Campaign', 'Draft Campaign', 'Disabled Campaign'):
            self.assertNotContains(response, hidden)
        self.assertContains(response, 'public_campaigns.css')

    def test_authenticated_alumni_keeps_existing_campaign_page(self):
        user = get_user_model().objects.create_user(
            username='registered-campaign-test', email='donor@example.com', password='password-12345')
        self.client.force_login(user)
        response = self.client.get(reverse('donations:campaign_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'donations/campaign_list.html')

    @patch('donations.forms.is_recaptcha_enabled', return_value=False)
    def test_public_donation_requires_valid_email_even_when_anonymous(self, recaptcha):
        data = {'amount': '100', 'donor_name': '', 'is_anonymous': 'on'}
        missing = DonationForm(data, campaign=self.open)
        self.assertFalse(missing.is_valid())
        self.assertIn('donor_email', missing.errors)
        invalid = DonationForm({**data, 'donor_email': 'invalid'}, campaign=self.open)
        self.assertFalse(invalid.is_valid())
        self.assertIn('donor_email', invalid.errors)
        valid = DonationForm({**data, 'donor_email': 'guest@example.com'}, campaign=self.open)
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertTrue(DonationForm(user=None, campaign=self.open).fields['donor_email'].required)


class DonationNotificationTests(TestCase):
    def setUp(self):
        category = CampaignType.objects.create(name='Notice Fund', slug='notice-fund-test')
        self.campaign = Campaign.objects.create(name='Notice test campaign', slug='notice-test',
            campaign_type=category, description='Donation notices', short_description='For testing',
            goal_amount=Decimal('10000.00'), visibility='public', status='active', allow_donations=True)
        self.donation = Donation.objects.create(campaign=self.campaign, amount=Decimal('100.00'),
            donor_email='guest-notice@example.com', status='pending_payment')

    @patch('donations.signals.send_donation_confirmation_email')
    @patch('donations.signals.send_donation_status_update_email')
    def test_proof_acknowledgement_sent_only_after_commit(self, status_mail, proof_mail):
        # A notification is permitted only when both pieces of payment evidence
        # have been persisted. Otherwise the hardened signal correctly skips it.
        image = BytesIO()
        Image.new('RGB', (8, 8), (255, 255, 255)).save(image, format='PNG')
        self.donation.reference_number = 'GCASH-COMMIT-TEST-123'
        self.donation.payment_proof = SimpleUploadedFile(
            'notice-proof.png', image.getvalue(), content_type='image/png',
        )
        self.donation.save(update_fields=['reference_number', 'payment_proof'])
        try:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                self.donation.status = 'pending_verification'
                self.donation.save(update_fields=['status'])
                proof_mail.assert_not_called()
            self.assertEqual(len(callbacks), 1)
            proof_mail.assert_called_once()
            status_mail.assert_not_called()
        finally:
            # FileField private storage is outside the transactional test DB.
            # Remove the uploaded fixture even if an assertion fails.
            self.donation.payment_proof.delete(save=False)

    @patch('donations.signals.send_donation_confirmation_email')
    def test_missing_proof_does_not_send_acknowledgement(self, proof_mail):
        with self.captureOnCommitCallbacks(execute=True):
            self.donation.status = 'pending_verification'
            self.donation.save(update_fields=['status'])
        proof_mail.assert_not_called()

    @patch('donations.signals.send_donation_receipt_email')
    @patch('donations.signals.send_donation_status_update_email')
    def test_staff_completion_triggers_status_and_receipt_after_commit(self, status_mail, receipt_mail):
        self.donation.status = 'pending_verification'
        self.donation.save(update_fields=['status'])
        status_mail.reset_mock()
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.donation.status = 'completed'
            self.donation.save(update_fields=['status'])
            status_mail.assert_not_called()
            receipt_mail.assert_not_called()
        self.assertEqual(len(callbacks), 1)
        status_mail.assert_called_once()
        receipt_mail.assert_called_once()

    @patch('donations.signals.send_donation_status_update_email')
    def test_admin_model_save_sends_notification(self, mail):
        user = get_user_model().objects.create_superuser(
            username='donation-admin-notices', email='staff@example.com', password='password-12345')
        request = self.client.request().wsgi_request
        request.user = user
        with self.captureOnCommitCallbacks(execute=True):
            self.donation.status = 'failed'
            admin.site._registry[Donation].save_model(request, self.donation, None, True)
        mail.assert_called_once()
        self.assertEqual(mail.call_args.args[1], 'pending_payment')

    @patch('donations.signals.send_donation_status_update_email')
    def test_unchanged_save_does_not_generate_extra_emails(self, mail):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.donation.save(update_fields=['message'])
        self.assertFalse(callbacks)
        mail.assert_not_called()

    @patch('donations.signals.send_donation_status_update_email')
    def test_rollback_does_not_send_email(self, mail):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    self.donation.status = 'failed'
                    self.donation.save(update_fields=['status'])
                    raise RuntimeError('Rollback test')
            except RuntimeError:
                pass
        self.assertEqual(callbacks, [])
        mail.assert_not_called()

    @patch('donations.email_utils.send_email_with_provider', return_value=True)
    def test_status_email_goes_to_guest_donor_email(self, provider):
        from .email_utils import send_donation_status_update_email
        self.donation.status = 'failed'
        self.assertTrue(send_donation_status_update_email(self.donation, 'pending_payment'))
        self.assertEqual(provider.call_args.kwargs['recipient_list'], ['guest-notice@example.com'])

    @patch('donations.signals.send_donation_status_update_email')
    def test_deleted_or_missing_email_never_claims_notification(self, mail):
        self.donation.donor_email = ''
        self.donation.save(update_fields=['donor_email'])
        with self.captureOnCommitCallbacks(execute=True):
            self.donation.status = 'failed'
            self.donation.save(update_fields=['status'])
        mail.assert_not_called()
