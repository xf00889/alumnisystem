"""Tracer-response employability, permissions, export and recovery regression tests."""
import json
from datetime import date, datetime
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni
from surveys.models import (Survey, SurveyQuestion, QuestionOption,
                            SurveyResponse, ResponseAnswer, EmploymentRecord)
from surveys.tracer_metadata import ALUMNI_TITLE

TEST_MIDDLEWARE = [m for m in settings.MIDDLEWARE if m != 'setup.middleware.SetupRequiredMiddleware']


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class EmployabilityReportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user('report-staff', 'staff@example.com', 'StrongPass123!', is_staff=True)
        self.visitor = User.objects.create_user('report-user', 'user@example.com', 'StrongPass123!')
        for user in (self.admin, self.visitor):
            user.profile.has_completed_registration = True
            user.profile.save(update_fields=['has_completed_registration'])
        self.a1 = self.create_alumni('first', 'MAIN', 'CAS')
        self.a2 = self.create_alumni('second', 'MAIN', 'CIT')
        self.a3 = self.create_alumni('third', 'BSC', 'CAS')
        self.extra = self.create_alumni('unanswered', 'BSC', 'CAS')
        self.survey = self.create_cycle()
        self.respond(self.survey, self.a1, 'Yes', '2026-02-02', '2026-04-15')
        self.respond(self.survey, self.a2, 'No', '', '2026-04-15')
        self.respond(self.survey, self.a3, 'Yes', '2026-09-12', '2026-09-14')
        # EmploymentRecord entries do not affect the tracer-response report.
        EmploymentRecord.objects.create(alumni=self.a1, company_name='Acme', job_title='Analyst',
                                        industry='IT', start_date=date(2026, 5, 3))

    def create_alumni(self, username, campus, college):
        user = get_user_model().objects.create_user(username, username+'@example.com', 'StrongPass123!')
        return Alumni.objects.create(user=user, campus=campus, college=college,
                                     course='Sample Program', graduation_year=2024,
                                     gender='M', province='Negros Oriental', city='Dumaguete', address='Test')

    def create_cycle(self):
        survey = Survey.objects.create(
            title=ALUMNI_TITLE, description='Test alumni tracer', created_by=self.admin,
            start_date=datetime(2025, 1, 1), end_date=datetime(2027, 12, 31), status='closed')
        for i, (key, text, kind) in enumerate((
            ('p2_year', 'Year Graduated', 'number'),
            ('p3_employed', 'Are you presently employed?', 'multiple_choice'),
            ('p3_current_job_start', 'Date you started your current job', 'date'),
        )):
            question = SurveyQuestion.objects.create(
                survey=survey, question_text=text, question_type=kind,
                display_order=i, help_text=json.dumps({'key': key}))
            if key == 'p3_employed':
                for order, label in enumerate(('Yes', 'No')):
                    QuestionOption.objects.create(question=question, option_text=label, display_order=order)
        return survey

    def respond(self, survey, alumni, employed, start, submitted_on):
        response = SurveyResponse.objects.create(survey=survey, alumni=alumni)
        SurveyResponse.objects.filter(pk=response.pk).update(submitted_at=datetime.fromisoformat(submitted_on))
        questions = {json.loads(q.help_text)['key']: q for q in survey.questions.prefetch_related('options')}
        ResponseAnswer.objects.create(response=response, question=questions['p2_year'], text_answer='2024')
        employment = questions['p3_employed']
        selected = next(o for o in employment.options.all() if o.option_text == employed)
        ResponseAnswer.objects.create(response=response, question=employment, selected_option=selected)
        if start:
            ResponseAnswer.objects.create(response=response, question=questions['p3_current_job_start'], text_answer=start)
        return response

    def get_over_https(self, url, params=None):
        return self.client.get(url, data=params, secure=True)

    def params(self):
        return {'cohort_year': 2024, 'report_year': 2026, 'as_of': '2026-09-30'}

    def test_anonymous_cannot_view(self):
        self.assertEqual(self.get_over_https(reverse('surveys:employability_report')).status_code, 302)

    def test_non_staff_cannot_view(self):
        self.client.force_login(self.visitor)
        self.assertEqual(self.get_over_https(reverse('surveys:employability_report')).status_code, 404)

    def test_counts_tracer_answers_and_ignores_unanswered_alumni(self):
        self.client.force_login(self.admin)
        result = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context['graduates'], 3)
        self.assertEqual(result.context['quarter_totals'], [1, 0, 1, 0])
        self.assertEqual(result.context['employed'], 2)
        self.assertEqual(result.context['total_hired'], 2)
        self.assertEqual(result.context['undated'], 0)
        self.assertContains(result, 'Main campus subtotal')
        self.assertContains(result, 'Tracer responses')

    @override_settings(USE_TZ=False, TIME_ZONE='Asia/Manila')
    def test_employability_loads_with_project_naive_datetime_setting(self):
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_hired'], 2)

    def test_export_files_and_source_provenance(self):
        self.client.force_login(self.admin)
        for fmt, ext in (('csv', 'csv'), ('excel', 'xlsx'), ('pdf', 'pdf')):
            with self.subTest(fmt=fmt):
                response = self.get_over_https(reverse('surveys:employability_report'), {**self.params(), 'format': fmt})
                self.assertEqual(response.status_code, 200)
                self.assertIn('annual_2026', response['Content-Disposition'])
                self.assertIn(ext, response['Content-Disposition'])
                self.assertGreater(len(response.content), 120)
        csv_result = self.get_over_https(reverse('surveys:employability_report'), {**self.params(), 'format': 'csv'})
        self.assertIn(b'UNIVERSITY TOTAL', csv_result.content)
        self.assertIn(b'Tracer respondents', csv_result.content)
        self.assertNotIn(b'first@example.com', csv_result.content)

    def test_employed_without_date_is_not_assigned_quarter(self):
        self.respond(self.create_cycle(), self.a3, 'Yes', '', '2026-09-20')
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(response.context['employed'], 2)
        self.assertEqual(response.context['undated'], 1)
        self.assertEqual(response.context['quarter_totals'], [1, 0, 0, 0])

    def test_later_survey_cycle_supersedes_earlier_answer(self):
        self.respond(self.create_cycle(), self.a1, 'No', '', '2026-08-02')
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(response.context['employed'], 1)
        self.assertEqual(response.context['quarter_totals'], [0, 0, 1, 0])

    def test_future_submission_not_counted_in_snapshot(self):
        SurveyResponse.objects.filter(alumni=self.a3).update(submitted_at=datetime(2026, 10, 20))
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(response.context['graduates'], 2)
        self.assertEqual(response.context['employed'], 1)

    def test_invalid_future_asof_rejected(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.get_over_https(reverse('surveys:employability_report'),
                                            {'as_of': '2999-01-01'}).status_code, 400)

    def test_non_destructive_command_adds_job_date_question(self):
        self.survey.questions.filter(help_text__contains='p3_current_job_start').delete()
        before = ResponseAnswer.objects.filter(response__survey=self.survey).count()
        call_command('add_tracer_job_start_question', verbosity=0)
        call_command('add_tracer_job_start_question', verbosity=0)
        job_qs = self.survey.questions.filter(help_text__contains='p3_current_job_start')
        self.assertEqual(job_qs.count(), 1)
        self.assertEqual(ResponseAnswer.objects.filter(response__survey=self.survey).count(), before - 2)
        self.assertEqual(json.loads(job_qs.get().help_text)['show_when'],
                         {str(self.survey.questions.get(help_text__contains='p3_employed').pk): ['yes']})

    def test_public_forgot_password_is_not_login_required(self):
        response = self.get_over_https(reverse('account_reset_password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email', status_code=200)
