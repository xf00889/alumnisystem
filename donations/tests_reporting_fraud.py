"""Financial-truth and fraud-review regression tests for the donations admin.

Run: python manage.py test donations.tests_reporting_fraud --verbosity 2
Never generates real payments or sends email.
"""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .fraud_detection import fraud_detector
from .models import BlacklistedEntity, Campaign, CampaignType, Donation, FraudAlert


class DonationIntelligenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username='report-admin', email='report-admin@example.com', password='test-pass-12345'
        )
        cls.donor = get_user_model().objects.create_user(
            username='report-donor', email='donor@example.com', password='test-pass-12345'
        )
        category = CampaignType.objects.create(name='Analytics test', slug='analytics-test')
        cls.campaign = Campaign.objects.create(
            name='Test scholarship', slug='test-scholarship', campaign_type=category,
            description='Reporting regression', short_description='Reporting regression',
            goal_amount=Decimal('10000.00'), status='active',
        )

    def setUp(self):
        bypass = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        bypass.start()
        self.addCleanup(bypass.stop)
        self.client.force_login(self.admin)

    def donation(self, amount, status, created_at=None):
        obj = Donation.objects.create(
            campaign=self.campaign, donor=self.donor, amount=Decimal(amount), status=status,
        )
        if created_at:
            Donation.objects.filter(pk=obj.pk).update(created_at=created_at)
        return obj

    def test_analytics_only_counts_verified_funds_and_respects_date_filter(self):
        self.donation('100.00', 'completed')
        self.donation('200.00', 'pending_verification')
        self.donation('300.00', 'failed')
        self.donation('400.00', 'refunded')
        self.donation('50.00', 'completed', timezone.now() - timedelta(days=100))
        with patch('donations.views.render') as render:
            render.return_value.status_code = 200
            self.client.get(reverse('donations:analytics_dashboard') + '?days=30')
            context = render.call_args.args[2]
        self.assertEqual(context['period_totals']['total_amount'], Decimal('100.00'))
        self.assertEqual(context['period_totals']['total_count'], 1)
        self.assertEqual(context['lifetime_totals']['total_amount'], Decimal('150.00'))
        self.assertEqual(sum(context['chart_data']['daily']['amounts']), 100.0)
        self.assertEqual(sum(context['chart_data']['payment']['amounts']), 100.0)
        self.assertEqual(context['campaign_performance'][0].total_raised, Decimal('100.00'))

    def test_empty_analytics_returns_empty_chart_arrays_without_fake_categories(self):
        with patch('donations.views.render') as render:
            render.return_value.status_code = 200
            self.client.get(reverse('donations:analytics_dashboard'))
            context = render.call_args.args[2]
        self.assertEqual(context['chart_data']['daily']['labels'], [])
        self.assertEqual(context['chart_data']['payment']['labels'], [])
        self.assertEqual(context['period_totals']['total_count'], 0)

    def test_analytics_period_rejects_unbounded_values(self):
        with patch('donations.views.render') as render:
            render.return_value.status_code = 200
            self.client.get(reverse('donations:analytics_dashboard') + '?days=-1000')
            self.assertEqual(render.call_args.args[2]['days'], 30)

    def test_fraud_view_limits_period_but_keeps_outstanding_items(self):
        donation = self.donation('100.00', 'pending_verification')
        FraudAlert.objects.create(
            donation=donation, alert_type='suspicious_amount', severity='high',
            description='Needs manual review',
        )
        with patch('donations.views.render') as render:
            render.return_value.status_code = 200
            self.client.get(reverse('donations:fraud_monitoring_dashboard') + '?days=invalid')
            context = render.call_args.args[2]
        self.assertEqual(context['days'], 30)
        self.assertEqual(context['pending_alerts'].count(), 1)
        self.assertEqual(context['high_risk_donations'].count(), 1)

    def test_fraud_review_requires_notes_and_records_reviewer(self):
        donation = self.donation('100.00', 'pending_verification')
        alert = FraudAlert.objects.create(
            donation=donation, alert_type='suspicious_amount', severity='high',
            description='Review test',
        )
        url = reverse('donations:resolve_fraud_alert', args=[alert.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {'status': 'resolved'}).status_code, 400)
        response = self.client.post(url, {'status': 'false_positive', 'notes': 'Receipt independently matched.'})
        self.assertEqual(response.status_code, 200)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'false_positive')
        self.assertEqual(alert.reviewed_by_id, self.admin.pk)
        self.assertEqual(alert.resolution_notes, 'Receipt independently matched.')

    def test_repeated_screening_does_not_duplicate_open_alert(self):
        donation = self.donation('65000.00', 'pending_verification')
        fraud_detector.analyze_donation(donation)
        fraud_detector.analyze_donation(donation)
        self.assertEqual(FraudAlert.objects.filter(donation=donation, alert_type='suspicious_amount').count(), 1)

    def test_blacklist_expiry_and_exact_matching(self):
        donation = self.donation('100.00', 'pending_verification')
        donation.donor_email = 'donor@example.com'
        donation.donor_name = 'Peter Parker'
        BlacklistedEntity.objects.create(
            entity_type='email', value='donor@example.com', reason='Expired',
            expires_at=timezone.now() - timedelta(days=1),
        )
        BlacklistedEntity.objects.create(
            entity_type='name', value='Peter P', reason='Should not partially match',
        )
        self.assertIsNone(fraud_detector.check_blacklisted_entities(donation, None))
        BlacklistedEntity.objects.create(
            entity_type='name', value='Peter Parker', reason='Exact match',
        )
        self.assertIn('Peter Parker', fraud_detector.check_blacklisted_entities(donation, None))

    def test_blacklist_crud_and_export_authorization(self):
        create_url = reverse('donations:create_blacklisted_entity')
        response = self.client.post(create_url, {
            'entity_type': 'email', 'value': 'SAMPLE@EXAMPLE.COM', 'reason': 'Screening review',
        })
        self.assertEqual(response.status_code, 302)
        entry = BlacklistedEntity.objects.get(value='sample@example.com')
        self.assertTrue(entry.is_active)
        self.client.post(reverse('donations:deactivate_blacklisted_entity', args=[entry.pk]))
        entry.refresh_from_db()
        self.assertFalse(entry.is_active)
        self.assertEqual(self.client.get(reverse('donations:export_fraud_alerts')).status_code, 200)
        self.client.force_login(self.donor)
        self.assertEqual(self.client.get(reverse('donations:analytics_dashboard')).status_code, 403)
        self.assertEqual(self.client.get(reverse('donations:export_fraud_alerts')).status_code, 403)
        self.assertEqual(self.client.post(create_url, {
            'entity_type':'email', 'value':'bad@example.com', 'reason':'x',
        }).status_code, 403)

    def test_campaign_totals_follow_completed_amount_edits_and_deletions(self):
        completed = self.donation('100.00', 'completed')
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.current_amount, Decimal('100.00'))
        completed.amount = Decimal('125.00')
        completed.save()
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.current_amount, Decimal('125.00'))
        completed.delete()
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.current_amount, Decimal('0.00'))

    def test_campaign_totals_recalculate_both_sides_on_campaign_move(self):
        other = Campaign.objects.create(
            name='Other campaign', slug='other-campaign',
            campaign_type=self.campaign.campaign_type,
            description='Other', short_description='Other', goal_amount=Decimal('1000'),
        )
        completed = self.donation('350.00', 'completed')
        completed.campaign = other
        completed.save()
        self.campaign.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.campaign.current_amount, Decimal('0.00'))
        self.assertEqual(other.current_amount, Decimal('350.00'))
