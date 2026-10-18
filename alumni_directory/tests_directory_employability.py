"""Regression coverage: directory reporting periods, filter scope and aggregate exports.

Run against an isolated test DB, not production.
"""
import json
from datetime import date, datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from alumni_directory.models import Alumni
from alumni_directory.directory_employability import build_directory_employability
from surveys.models import Survey, SurveyQuestion, SurveyResponse, ResponseAnswer, QuestionOption
from surveys.tracer_metadata import ALUMNI_TITLE
from core.models.coordinator_campus import CoordinatorCampus

TEST_MIDDLEWARE = [m for m in settings.MIDDLEWARE if m != 'setup.middleware.SetupRequiredMiddleware']


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False, USE_TZ=False)
class DirectoryEmployabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser('employability-admin', 'e-admin@example.com', 'StrongPass123!')
        cls.member = User.objects.create_user('employability-member', 'e-member@example.com', 'StrongPass123!')
        cls.coordinator = User.objects.create_user('employability-coord', 'e-coord@example.com', 'StrongPass123!')
        cls.coordinator.profile.is_alumni_coordinator = True
        cls.coordinator.profile.save(update_fields=['is_alumni_coordinator'])
        CoordinatorCampus.objects.create(user=cls.coordinator, campus='MAIN')
        for user in (cls.admin, cls.member, cls.coordinator):
            user.profile.has_completed_registration = True
            user.profile.save(update_fields=['has_completed_registration'])

        def alumnus(name, *, year=2024, college='CTE', course='BEED', campus='MAIN'):
            user = User.objects.create_user(f'employability-{name}', f'e-{name}@example.com', 'StrongPass123!')
            return Alumni.objects.create(user=user, graduation_year=year, college=college,
                                         course=course, campus=campus, gender='F',
                                         province='Negros Oriental', city='Dumaguete', address='Test')

        cls.alice = alumnus('alice')
        cls.betty = alumnus('betty')
        cls.carla = alumnus('carla', course='BSED')
        cls.donna = alumnus('donna', year=2025)
        cls.bsc = alumnus('bsc', campus='BSC')
        cls.unanswered = alumnus('unanswered')
        cls.survey = Survey.objects.create(
            title=ALUMNI_TITLE, description='Sample tracer', created_by=cls.admin,
            start_date=datetime(2024, 1, 1), end_date=datetime(2026, 12, 31), status='closed',
        )
        questions = {}
        for order, (key, question_type) in enumerate((
            ('p3_employed', 'multiple_choice'), ('p3_current_job_start', 'date'),
        )):
            q = SurveyQuestion.objects.create(
                survey=cls.survey, question_text=key, question_type=question_type,
                display_order=order, help_text=json.dumps({'key': key}),
            )
            questions[key] = q
        for order, label in enumerate(('Yes', 'No')):
            QuestionOption.objects.create(question=questions['p3_employed'], option_text=label, display_order=order)

        def respondent(alumni, employed, started, submitted):
            response = SurveyResponse.objects.create(survey=cls.survey, alumni=alumni)
            SurveyResponse.objects.filter(pk=response.pk).update(submitted_at=datetime.fromisoformat(submitted))
            option = questions['p3_employed'].options.get(option_text=employed)
            ResponseAnswer.objects.create(response=response, question=questions['p3_employed'], selected_option=option)
            if started:
                ResponseAnswer.objects.create(response=response, question=questions['p3_current_job_start'], text_answer=started)
        respondent(cls.alice, 'Yes', '2025-02-11', '2025-03-02')
        respondent(cls.betty, 'No', None, '2025-05-03')
        respondent(cls.carla, 'Yes', '2025-03-02', '2025-03-03')
        respondent(cls.donna, 'Yes', '2025-02-09', '2025-03-04')
        respondent(cls.bsc, 'Yes', '2025-02-20', '2025-03-05')

    def params(self, **kwargs):
        return {'graduation_year': '2024', 'college': 'CTE', 'course': 'BEED',
                'period': 'quarterly', 'year': '2025', 'quarter': '1', 'employability': '1', **kwargs}

    def test_snapshot_rates_change_with_reporting_period(self):
        eligible = Alumni.objects.filter(graduation_year=2024, college='CTE', course='BEED', campus='MAIN')
        q1 = build_directory_employability(eligible, self.params(), today=date(2026, 10, 18))
        q2 = build_directory_employability(eligible, self.params(quarter='2'), today=date(2026, 10, 18))
        self.assertEqual((q1['eligible_total'], q1['graduates'], q1['employed'], q1['total_hired']), (3, 1, 1, 1))
        self.assertEqual(q1['rate'], 100)
        self.assertEqual((q2['graduates'], q2['employed'], q2['total_hired']), (2, 1, 0))
        self.assertEqual(q2['rate'], 50)
        self.assertEqual(q1['as_of'], date(2025, 3, 31))
        self.assertEqual(q2['as_of'], date(2025, 6, 30))

    def test_period_modes(self):
        eligible = Alumni.objects.filter(pk=self.alice.pk)
        for mode, selections, expected_starts in (
            ('monthly', {'month': '2'}, 0),  # response only arrived in March
            ('quarterly', {'quarter': '1'}, 1),
            ('semi_annual', {'half': '1'}, 1),
            ('annual', {}, 1),
        ):
            with self.subTest(mode=mode):
                report = build_directory_employability(
                    eligible, self.params(period=mode, **selections), today=date(2026, 10, 18))
                self.assertEqual(report['total_hired'], expected_starts)
                self.assertEqual(report['period_kind'], mode)

    def test_directory_renders_staff_only_panel_and_preserves_filters(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('alumni_directory:alumni_list'), self.params(), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_registered'], 4)  # includes BSC, excludes other course/year
        self.assertEqual(response.context['employability_report']['graduates'], 2)
        self.assertContains(response, 'Employability report')
        self.assertContains(response, 'employability/export/')
        self.assertContains(response, 'name="college" value="CTE"')
        self.client.force_login(self.member)
        other = self.client.get(reverse('alumni_directory:alumni_list'), self.params(), secure=True)
        self.assertEqual(other.status_code, 200)
        self.assertNotContains(other, 'directoryEmployabilityForm')

    def test_coordinator_export_scoped_to_assigned_campus(self):
        self.client.force_login(self.coordinator)
        response = self.client.get(reverse('alumni_directory:employability_export'),
                                   self.params(format='csv'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'UNIVERSITY TOTAL,1', response.content)  # Q1 only Alice responded in MAIN
        self.assertNotIn(b'bsc@example.com', response.content)

    def test_non_staff_and_anonymous_exports_denied(self):
        endpoint = reverse('alumni_directory:employability_export')
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(endpoint, self.params(format='csv'), secure=True).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(endpoint, self.params(format='csv'), secure=True).status_code, 302)

    def test_exports_reuse_csv_excel_pdf_and_remain_aggregated(self):
        self.client.force_login(self.admin)
        endpoint = reverse('alumni_directory:employability_export')
        for fmt, mime in (
            ('csv', 'text/csv'), ('excel', 'spreadsheetml.sheet'), ('pdf', 'application/pdf'),
        ):
            with self.subTest(fmt=fmt):
                response = self.client.get(endpoint, self.params(format=fmt), secure=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(mime, response['Content-Type'])
                self.assertIn('quarterly_2025-Q1', response['Content-Disposition'])
                self.assertGreater(len(response.content), 80)
        response = self.client.get(endpoint, self.params(format='csv'), secure=True)
        self.assertIn(b'Program: BEED', response.content)
        self.assertNotIn(b'e-alice@example.com', response.content)

    def test_no_tracer_responses_is_not_reported_as_zero_percent(self):
        report = build_directory_employability(
            Alumni.objects.filter(pk=self.alice.pk),
            self.params(period='monthly', month='1'), today=date(2026, 10, 18),
        )
        self.assertEqual(report['employment_rate_display'], 'N/A')
        self.assertEqual(report['graduates'], 0)

    def test_future_period_and_missing_cohort_rejected(self):
        eligible = Alumni.objects.filter(graduation_year=2024)
        with self.assertRaises(ValueError):
            build_directory_employability(eligible, self.params(period='annual', year='2027'), today=date(2026, 10, 18))
        with self.assertRaises(ValueError):
            build_directory_employability(eligible, {'period': 'annual', 'year': '2025'}, today=date(2026, 10, 18))
