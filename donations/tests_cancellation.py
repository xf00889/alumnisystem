"""Regression coverage for alumni donation cancellation and history visibility."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import Campaign, CampaignType, Donation


class DonorCancellationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username='cancel-owner', password='test-password-123')
        self.other = user_model.objects.create_user(username='cancel-other', password='test-password-123')
        category = CampaignType.objects.create(name='Giving', slug='cancel-giving')
        self.campaign = Campaign.objects.create(
            name='Cancellation test', slug='cancel-campaign', campaign_type=category,
            description='Testing cancellation', short_description='Testing',
            goal_amount=Decimal('10000.00'), status='active', visibility='public',
        )
        self.pending = Donation.objects.create(
            donor=self.owner, campaign=self.campaign, amount=Decimal('100.00'), status='pending_payment',
        )
        self.history_url = reverse('donations:donation_history')
        self.cancel_url = reverse('donations:cancel_donation', args=[self.pending.pk])
        self.client.force_login(self.owner)

    def test_owner_can_cancel_unpaid_donation_and_hide_it_in_history(self):
        response = self.client.post(self.cancel_url)
        self.assertRedirects(response, self.history_url)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'cancelled')
        self.assertTrue(Donation.objects.filter(pk=self.pending.pk).exists())
        history = self.client.get(self.history_url)
        self.assertNotIn(self.pending, list(history.context['donations']))
        self.assertEqual(history.context['donation_count'], 0)

    def test_get_cannot_cancel(self):
        self.assertEqual(self.client.get(self.cancel_url).status_code, 405)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'pending_payment')

    def test_other_user_cannot_cancel_someones_donation(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.cancel_url).status_code, 404)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'pending_payment')

    def test_anonymous_user_cannot_cancel(self):
        self.client.logout()
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, 302)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'pending_payment')

    def test_proof_submitted_donation_cannot_be_cancelled(self):
        self.pending.status = 'pending_verification'
        self.pending.reference_number = 'GCASH-100001'
        self.pending.save()
        self.assertRedirects(self.client.post(self.cancel_url), self.history_url)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'pending_verification')
        self.assertIn(self.pending, list(self.client.get(self.history_url).context['donations']))

    def test_reference_already_recorded_blocks_cancellation_even_if_pending_payment(self):
        self.pending.reference_number = 'GCASH-100002'
        self.pending.save()
        self.client.post(self.cancel_url)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'pending_payment')

    def test_completed_donation_cannot_be_cancelled(self):
        self.pending.status = 'completed'
        self.pending.save()
        self.client.post(self.cancel_url)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'completed')
        self.assertEqual(self.campaign.donations.filter(status='completed').count(), 1)

    def test_repeat_cancellation_is_harmless(self):
        self.client.post(self.cancel_url)
        self.client.post(self.cancel_url)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, 'cancelled')
