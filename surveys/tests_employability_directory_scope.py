"""Selected directory academic filters carry through report calculations and exports."""
import csv
import json
from datetime import datetime
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni
from core.models.coordinator_campus import CoordinatorCampus
from surveys.models import Survey, SurveyQuestion, QuestionOption, SurveyResponse, ResponseAnswer
from surveys.tracer_metadata import ALUMNI_TITLE


@override_settings(MIDDLEWARE=[m for m in settings.MIDDLEWARE
                              if m != 'setup.middleware.SetupRequiredMiddleware'])
class EmployabilityDirectoryScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user('scope-staff', 'scope-staff@example.com',
                                             'strong-pass', is_staff=True)
        cls.coordinator = User.objects.create_user('scope-coordinator',
                                                   'scope-coordinator@example.com', 'strong-pass')
        cls.coordinator.profile.is_alumni_coordinator = True
        cls.coordinator.profile.save(update_fields=['is_alumni_coordinator'])
        CoordinatorCampus.objects.create(user=cls.coordinator, campus='BSC')
        survey = Survey.objects.create(
            title=ALUMNI_TITLE, description='Report filter test', created_by=cls.staff,
            start_date=datetime(2025, 1, 1), end_date=datetime(2027, 12, 31),
            status='closed',
        )
        questions = {}
        for order, (key, text, kind) in enumerate([
            ('p2_year', 'Graduating year', 'number'),
            ('p3_employed', 'Currently employed?', 'multiple_choice'),
            ('p3_current_job_start', 'Current job start date', 'date'),
        ]):
            questions[key] = SurveyQuestion.objects.create(
                survey=survey, question_text=text, question_type=kind,
                display_order=order, help_text=json.dumps({'key': key}),
            )
        yes = QuestionOption.objects.create(question=questions['p3_employed'],
                                            option_text='Yes', display_order=0)
        no = QuestionOption.objects.create(question=questions['p3_employed'],
                                           option_text='No', display_order=1)
        for i, (campus, college, course, employed) in enumerate([
            ('BSC', 'CTE', 'BEED', True),
            ('BSC', 'CTE', 'BSED', False),
            ('MAIN', 'CAS', 'BSINT', True),
            ('MAIN', 'CTE', 'BEED', True),
        ]):
            account = User.objects.create_user(
                username=f'scope-member-{i}', email=f'scope-member-{i}@example.com',
                password='strong-pass',
            )
            alumni = Alumni.objects.create(
                user=account, campus=campus, college=college,
                course=course, graduation_year=2025, gender='M',
                province='Negros Oriental', city='Bayawan', address='Test',
            )
            response = SurveyResponse.objects.create(survey=survey, alumni=alumni)
            SurveyResponse.objects.filter(pk=response.pk).update(
                submitted_at=datetime(2026, 4, 15),
            )
            ResponseAnswer.objects.create(response=response, question=questions['p2_year'],
                                          text_answer='2025')
            ResponseAnswer.objects.create(response=response, question=questions['p3_employed'],
                                          selected_option=yes if employed else no)
            if employed:
                ResponseAnswer.objects.create(
                    response=response, question=questions['p3_current_job_start'],
                    text_answer='2026-02-12',
                )

    def params(self, **extra):
        return {
            'cohort_year': '2025', 'report_year': '2026', 'as_of': '2026-09-30',
            **extra,
        }

    def test_all_reports_and_selected_college_program(self):
        self.client.force_login(self.staff)
        url = reverse('surveys:employability_report')
        broad = self.client.get(url, self.params(), secure=True)
        self.assertEqual(broad.status_code, 200)
        self.assertEqual(broad.context['graduates'], 4)
        selected = self.client.get(url, self.params(college='CTE', course='BEED'), secure=True)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.context['graduates'], 2)
        self.assertEqual(selected.context['employed'], 2)
        self.assertEqual(selected.context['scope_total_label'], 'Filtered total')
        self.assertContains(selected, 'Filtered total')
        bsc = self.client.get(url, self.params(college='CTE', course='BEED', campus='BSC'), secure=True)
        self.assertEqual(bsc.context['graduates'], 1)
        self.assertEqual(bsc.context['employed'], 1)
        self.assertEqual(bsc.context['total_hired'], 1)

    def test_exports_share_exact_scope(self):
        self.client.force_login(self.staff)
        selected = self.params(college='CTE', course='BEED', campus='BSC')
        for fmt in ('csv', 'excel', 'pdf'):
            with self.subTest(fmt=fmt):
                response = self.client.get(reverse('surveys:employability_report'),
                                           {**selected, 'format': fmt}, secure=True)
                self.assertEqual(response.status_code, 200)
                self.assertGreater(len(response.content), 100)
        response = self.client.get(reverse('surveys:employability_report'),
                                   {**selected, 'format': 'csv'}, secure=True)
        rows = list(csv.reader(StringIO(response.content.decode('utf-8'))))
        self.assertTrue(any('BEED' in row for row in rows))
        self.assertTrue(any('FILTERED TOTAL' in row and '1' in row for row in rows))

    def test_invalid_college_rejected(self):
        self.client.force_login(self.staff)
        result = self.client.get(reverse('surveys:employability_report'),
                                 self.params(college='INVALID'), secure=True)
        self.assertEqual(result.status_code, 400)

    def test_coordinator_cannot_access_unassigned_campus(self):
        self.client.force_login(self.coordinator)
        url = reverse('surveys:employability_report')
        result = self.client.get(url, self.params(), secure=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context['graduates'], 2)
        outside = self.client.get(url, self.params(campus='MAIN'), secure=True)
        self.assertEqual(outside.context['graduates'], 0)
