"""Donation staff review regression tests.

Run with proof tests:
python manage.py test donations.tests_verification_actions donations.tests_proof_integrity --keepdb

The setup middleware bypass below applies only to the isolated test database;
production setup, permissions, GCash reconciliation and CSRF remain unchanged.
"""
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Campaign, CampaignType, Donation


class DonationVerificationActionTests(TestCase):
    def setUp(self):
        setup_check = patch(
            'setup.middleware.SetupRequiredMiddleware._is_setup_complete',
            return_value=True,
        )
        setup_check.start()
        self.addCleanup(setup_check.stop)

        User = get_user_model()
        self.staff = User.objects.create_superuser(
            username='review-test-admin', email='review-admin@example.com',
            password='review-test-password',
        )
        self.other_user = User.objects.create_user(
            username='review-test-donor', email='donor@example.com',
            password='review-test-password',
        )
        category = CampaignType.objects.create(
            name='Review Regression', slug='review-regression-test',
        )
        campaign = Campaign.objects.create(
            name='Review Regression Campaign', slug='review-regression-campaign',
            campaign_type=category, description='Test campaign',
            short_description='Test campaign', goal_amount=Decimal('5000.00'),
            status='active', visibility='public', allow_donations=True,
        )
        buffer = BytesIO()
        Image.new('RGB', (10, 10), (240, 240, 240)).save(buffer, format='PNG')
        self.donation = Donation.objects.create(
            campaign=campaign, donor=self.other_user, amount=Decimal('1000.00'),
            status='pending_verification', reference_number='GCASH-REVIEW-12345',
            payment_proof=SimpleUploadedFile(
                'review-fixture.png', buffer.getvalue(), content_type='image/png',
            ),
        )
        self.url = reverse('donations:verify_donation', kwargs={'pk': self.donation.pk})
        self.client.force_login(self.staff)

    def tearDown(self):
        # FileField storage is not rolled back with the test database.
        self.donation.refresh_from_db()
        if self.donation.payment_proof:
            self.donation.payment_proof.delete(save=False)

    def test_staff_can_approve_after_confirmed_reconciliation(self):
        response = self.client.post(self.url, {
            'status': 'completed', 'verification_notes': 'GCash credit matched',
            'gcash_reconciled': 'yes',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'completed')
        self.assertEqual(self.donation.verification_notes, 'GCash credit matched')
        self.assertEqual(self.donation.verified_by_id, self.staff.pk)

    def test_approval_without_manual_reconciliation_is_rejected(self):
        response = self.client.post(self.url, {'status': 'completed'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'pending_verification')

    def test_approval_without_saved_reference_or_proof_is_rejected(self):
        self.donation.reference_number = ''
        self.donation.save(update_fields=['reference_number'])
        response = self.client.post(self.url, {
            'status': 'completed', 'gcash_reconciled': 'yes',
        })
        self.assertEqual(response.status_code, 400)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'pending_verification')

    def test_staff_can_reject(self):
        response = self.client.post(self.url, {
            'status': 'failed', 'verification_notes': 'Reference mismatch',
        })
        self.assertEqual(response.status_code, 200)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'failed')
        self.assertEqual(self.donation.verification_notes, 'Reference mismatch')

    def test_staff_can_dispute(self):
        response = self.client.post(self.url, {
            'status': 'disputed', 'verification_notes': 'Needs manual review',
        })
        self.assertEqual(response.status_code, 200)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'disputed')

    def test_non_staff_cannot_change_donation_status(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url, {
            'status': 'completed', 'gcash_reconciled': 'yes',
        })
        self.assertEqual(response.status_code, 403)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'pending_verification')

    def test_get_does_not_change_status(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'pending_verification')

    def test_repeated_review_of_completed_donation_is_blocked(self):
        self.donation.status = 'completed'
        self.donation.save(update_fields=['status'])
        response = self.client.post(self.url, {'status': 'failed'})
        self.assertEqual(response.status_code, 409)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'completed')
