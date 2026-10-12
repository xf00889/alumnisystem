"""Regression tests for donor access, recipient selection and payment intents."""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.backends.cached_db import SessionStore
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, RequestFactory
from django.utils import timezone

from .models import Campaign, CampaignType, Donation, GCashConfig
from .payment_flow import (
    assert_campaign_accepts_donations, assert_donation_access, grant_guest_access,
    resolve_recipient, signed_guest_token,
)


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.alumni = get_user_model().objects.create_user(username='donor-test', password='test12345')
        self.stranger = get_user_model().objects.create_user(username='stranger-test', password='test12345')
        self.campaign_type = CampaignType.objects.create(name='Scholarship', slug='donation-test')
        self.payee = GCashConfig.objects.create(
            name='Scholarship GCash', account_name='University', gcash_number='09123456789',
            qr_code_image='gcash_qr/test.png', is_active=True)
        self.other = GCashConfig.objects.create(
            name='Other account', account_name='Different', gcash_number='09999999999',
            qr_code_image='gcash_qr/other.png', is_active=True)
        self.campaign = Campaign.objects.create(
            name='Scholarship donation', slug='scholarship-donation',
            campaign_type=self.campaign_type, description='Description', short_description='Description',
            goal_amount=Decimal('5000.00'), gcash_config=self.payee, visibility='public',
            status='active', allow_donations=True)
        self.donation = Donation.objects.create(
            donor=self.alumni, campaign=self.campaign, amount=Decimal('500.00'))
        self.guest = Donation.objects.create(
            donor_email='guest@example.com', campaign=self.campaign, amount=Decimal('150.00'))
        self.factory = RequestFactory()

    def request(self, user, query=None):
        req = self.factory.get('/donations/payment/', data=query or {})
        req.user = user
        req.session = SessionBase()
        return req

    def test_owner_can_access(self):
        assert_donation_access(self.request(self.alumni), self.donation)

    def test_other_alumni_cannot_read_donation(self):
        with self.assertRaises(PermissionDenied):
            assert_donation_access(self.request(self.stranger), self.donation)

    def test_numeric_guest_donation_id_is_not_a_grant(self):
        with self.assertRaises(PermissionDenied):
            assert_donation_access(self.request(AnonymousUser()), self.guest)

    def test_guest_session_access(self):
        request = self.request(AnonymousUser())
        grant_guest_access(request, self.guest)
        assert_donation_access(request, self.guest)

    def test_signed_guest_recovery_and_tampered_signature(self):
        token = signed_guest_token(self.guest)
        assert_donation_access(self.request(AnonymousUser(), {'access': token}), self.guest)
        with self.assertRaises(PermissionDenied):
            assert_donation_access(self.request(AnonymousUser(), {'access': token + 'invalid'}), self.guest)

    def test_guest_get_claim_survives_lost_session(self):
        claim = signed_guest_token(self.guest)
        request = self.request(AnonymousUser(), {'access': claim})
        assert_donation_access(request, self.guest)
        self.assertIn(self.guest.pk, request.session['guest_donations_owned'])

    def test_guest_post_claim_survives_lost_session(self):
        # A guest can have a valid proof page open while a cache-backed
        # session expires or a local development server restarts.
        claim = signed_guest_token(self.guest)
        request = self.factory.post('/donations/upload-proof/%s/' % self.guest.pk,
                                    data={'access': claim})
        request.user = AnonymousUser()
        request.session = SessionBase()
        assert_donation_access(request, self.guest)
        self.assertIn(self.guest.pk, request.session['guest_donations_owned'])

    def test_guest_post_claim_does_not_authorize_other_donation(self):
        claim = signed_guest_token(self.guest)
        request = self.factory.post('/donations/upload-proof/%s/' % self.donation.pk,
                                    data={'access': claim})
        request.user = AnonymousUser()
        request.session = SessionBase()
        with self.assertRaises(PermissionDenied):
            assert_donation_access(request, self.donation)

    def test_guest_post_rejects_tampered_claim(self):
        claim = signed_guest_token(self.guest) + 'invalid'
        request = self.factory.post('/donations/upload-proof/%s/' % self.guest.pk,
                                    data={'access': claim})
        request.user = AnonymousUser()
        request.session = SessionBase()
        with self.assertRaises(PermissionDenied):
            assert_donation_access(request, self.guest)

    def test_registered_donation_denies_guest_claim(self):
        claim = signed_guest_token(self.donation)
        request = self.factory.post('/donations/upload-proof/%s/' % self.donation.pk,
                                    data={'access': claim})
        request.user = AnonymousUser()
        request.session = SessionBase()
        with self.assertRaises(PermissionDenied):
            assert_donation_access(request, self.donation)

    def test_campaign_assigned_payee_wins_over_global_config(self):
        self.assertEqual(resolve_recipient(self.campaign).pk, self.payee.pk)

    def test_inactive_assigned_payee_cannot_fallback_to_other_account(self):
        self.payee.is_active = False
        self.payee.save(update_fields=['is_active'])
        with self.assertRaises(ValidationError):
            resolve_recipient(self.campaign)

    def test_disabled_or_ended_campaign_cannot_receive_new_intent(self):
        self.campaign.allow_donations = False
        with self.assertRaises(ValidationError):
            assert_campaign_accepts_donations(self.campaign, self.alumni)
        self.campaign.allow_donations = True
        self.campaign.end_date = timezone.now() - timedelta(minutes=1)
        with self.assertRaises(ValidationError):
            assert_campaign_accepts_donations(self.campaign, self.alumni)

    def test_registered_only_campaign_denies_anonymous(self):
        self.campaign.visibility = 'registered_alumni'
        with self.assertRaises(PermissionDenied):
            assert_campaign_accepts_donations(self.campaign, AnonymousUser())


class DonationSessionTests(TestCase):
    def test_session_survives_process_local_cache_loss(self):
        self.assertEqual(settings.SESSION_ENGINE, 'django.contrib.sessions.backends.cached_db')
        session = SessionStore()
        session['donation_id'] = 4
        session.save()

        cache.clear()

        restored = SessionStore(session_key=session.session_key)
        self.assertEqual(restored['donation_id'], 4)
