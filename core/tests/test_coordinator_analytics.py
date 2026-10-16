"""Regression guard: every alumni analytics chart is restricted to assigned campuses."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni
from core.models.coordinator_campus import CoordinatorCampus


@override_settings(SECURE_SSL_REDIRECT=False)
class CoordinatorAnalyticsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        guard.start()
        cls.addClassCleanup(guard.stop)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.coordinator = User.objects.create_user(username='analytics-coordinator', password='StrongPass!2026')
        cls.coordinator.profile.is_alumni_coordinator = True
        cls.coordinator.profile.save(update_fields=['is_alumni_coordinator'])
        CoordinatorCampus.objects.create(user=cls.coordinator, campus='MAIN')
        for idx, campus in enumerate(('MAIN', 'MAIN', 'BSC')):
            member = User.objects.create_user(username=f'analytics-alumni-{idx}', password='StrongPass!2026')
            Alumni.objects.create(user=member, campus=campus, college='CAS' if idx != 2 else 'CEA',
                                  graduation_year=2022 if idx != 2 else 2024, course='Sample course', gender='M')

    def test_campus_charts_exclude_alumni_in_unassigned_campuses(self):
        self.client.force_login(self.coordinator)
        response = self.client.get(reverse('core:coordinator_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_alumni'], 2)
        for key in ('campus_chart', 'college_chart', 'batch_chart', 'employment_chart'):
            with self.subTest(chart=key):
                self.assertEqual(sum(response.context[key]['values']), 2)
        self.assertNotIn('CEA · Engineering', response.context['college_chart']['labels'])
        self.assertEqual(len(response.context['registration_chart']['labels']), 6)
        self.assertContains(response, 'admin-page-header')
        self.assertContains(response, 'coordinator-college-data')
