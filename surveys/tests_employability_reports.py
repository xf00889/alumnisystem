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

    def test_monthly_report_displays_only_requested_month(self):
        self.client.force_login(self.admin)
        params = {**self.params(), 'period': 'monthly', 'year': 2026, 'month': 2}
        response = self.get_over_https(reverse('surveys:employability_report'), params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['period_labels'], ['February 2026'])
        self.assertEqual(response.context['period_totals'], [1])
        self.assertEqual(response.context['table_column_count'], 8)
        self.assertEqual(response.context['period_start_rate_display'], '33.33%')
        # The historical February graph must not use September's as-of employed values.
        campus_rows = response.context['rows']
        self.assertEqual(sum(row['total_hired'] for row in campus_rows), 1)
        self.assertEqual(sum(row['employed'] for row in campus_rows), 2)
        self.assertContains(response, 'Current-job starts by campus / college · February 2026')
        self.assertContains(response, 'Dated current-job starts · February 2026')
        self.assertContains(response, 'Current-job starts · February 2026')
        self.assertNotContains(response, 'Current-job starts · Q2 2026')
        self.assertContains(response, 'not a historical employment measure')
        csv_response = self.get_over_https(reverse('surveys:employability_report'), {**params, 'format': 'csv'})
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn(b'February 2026', csv_response.content)
        self.assertNotIn(b'Q2 2026', csv_response.content)
        self.assertIn(b'monthly_2026-02', csv_response['Content-Disposition'])

    def test_quarterly_and_half_year_report_single_requested_window(self):
        self.client.force_login(self.admin)
        checks = (
            ('quarterly', {'quarter': 1}, 'Q1 2026', [1]),
            ('quarterly', {'quarter': 3}, 'Q3 2026', [1]),
            ('semi_annual', {'half': 1}, 'H1 2026', [1]),
            ('semi_annual', {'half': 2}, 'H2 2026', [1]),
        )
        for kind, controls, label, expected in checks:
            with self.subTest(kind=kind, label=label):
                response = self.get_over_https(reverse('surveys:employability_report'), {
                    **self.params(), 'period': kind, 'year': 2026, **controls,
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['period_labels'], [label])
                self.assertEqual(response.context['period_totals'], expected)
                self.assertEqual(response.context['total_hired'], sum(expected))
                self.assertEqual(response.context['table_column_count'], 8)

    def test_annual_remains_four_quarters_and_excel_columns_match(self):
        from openpyxl import load_workbook
        self.client.force_login(self.admin)
        params = {**self.params(), 'period': 'annual', 'year': 2026}
        response = self.get_over_https(reverse('surveys:employability_report'), params)
        self.assertEqual(response.context['period_labels'],
                         ['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'])
        self.assertEqual(response.context['period_totals'], [1, 0, 1, 0])
        self.assertEqual(response.context['table_column_count'], 14)
        csv_response = self.get_over_https(reverse('surveys:employability_report'), {**params, 'format': 'csv'})
        for quarter in ('Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026'):
            self.assertIn(quarter.encode(), csv_response.content)
        workbook_response = self.get_over_https(reverse('surveys:employability_report'), {
            **self.params(), 'period': 'monthly', 'year': 2026, 'month': 2, 'format': 'excel'
        })
        sheet = load_workbook(BytesIO(workbook_response.content)).active
        self.assertEqual(sheet.max_column, 8)
        self.assertIn('February 2026', sheet.cell(5, 3).value)
        self.assertEqual(sheet.auto_filter.ref.split(':')[-1][0], 'H')

    def test_empty_cohort_rate_is_na_and_period_cannot_be_after_asof(self):
        self.client.force_login(self.admin)
        empty = self.get_over_https(reverse('surveys:employability_report'), {
            **self.params(), 'cohort_year': 2025, 'period': 'monthly', 'year': 2026, 'month': 2
        })
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.context['rate_display'], 'N/A')
        self.assertContains(empty, 'N/A')
        future_period = self.get_over_https(reverse('surveys:employability_report'), {
            **self.params(), 'period': 'monthly', 'year': 2026, 'month': 10
        })
        self.assertEqual(future_period.status_code, 400)


    def test_employability_filter_excludes_one_day_but_other_reports_keep_it(self):
        from django.template.loader import render_to_string

        self.client.force_login(self.admin)
        report = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(report.status_code, 200)
        html = report.content.decode('utf-8')
        self.assertNotIn('value="day"', html)
        self.assertNotIn('data-period-field="day"', html)
        for period in ('monthly', 'quarterly', 'semi_annual', 'annual', 'custom'):
            self.assertIn(f'value="{period}"', html)

        shared_html = render_to_string('admin/components/report_period_fields.html', {
            'period_kind': 'day',
        })
        self.assertIn('value="day"', shared_html)
        self.assertIn('data-period-field="day"', shared_html)

    def test_one_day_requests_are_rejected_even_when_entered_directly(self):
        self.client.force_login(self.admin)
        url = reverse('surveys:employability_report')
        for mode in ('day', 'one_day', 'single_day'):
            with self.subTest(period=mode):
                params = {**self.params(), 'period': mode, 'day': '2026-02-02'}
                report = self.get_over_https(url, params)
                self.assertEqual(report.status_code, 400)
                self.assertIn(b'One-day employability reports are not available', report.content)
                self.assertEqual(report.context['period_kind'], 'annual')
                export = self.get_over_https(url, {**params, 'format': 'csv'})
                self.assertEqual(export.status_code, 400)
                self.assertNotIn('Content-Disposition', export.headers)

    def test_single_day_custom_range_rejected_but_multi_day_custom_allowed(self):
        self.client.force_login(self.admin)
        url = reverse('surveys:employability_report')
        params = {
            **self.params(), 'period': 'custom',
            'start_date': '2026-02-02', 'end_date': '2026-02-02',
        }
        one_day = self.get_over_https(url, params)
        self.assertEqual(one_day.status_code, 400)
        self.assertIn(b'One-day employability reports are not available', one_day.content)

        valid_range = self.get_over_https(url, {
            **params, 'end_date': '2026-02-03',
        })
        self.assertEqual(valid_range.status_code, 200)
        self.assertEqual(valid_range.context['period_kind'], 'custom')
        self.assertEqual(len(valid_range.context['period_labels']), 1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class EmployabilityClarityTests(TestCase):
    setUp = EmployabilityReportTests.setUp
    create_alumni = EmployabilityReportTests.create_alumni
    create_cycle = EmployabilityReportTests.create_cycle
    respond = EmployabilityReportTests.respond
    get_over_https = EmployabilityReportTests.get_over_https
    params = EmployabilityReportTests.params
    """Regression coverage for new filter clearing, missing-job-date explanation and shares."""

    def test_report_has_clear_filters_link_to_unfiltered_report(self):
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), {
            **self.params(), 'period': 'monthly', 'year': 2026, 'month': 2, 'campus': 'MAIN'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clear filters')
        self.assertContains(response, f'href="{reverse("surveys:employability_report")}"')
        self.assertNotContains(response, 'Dates filter each data type by its relevant date')
        self.assertContains(response, 'Select the period for recorded current-job start dates')

    def test_undated_employment_has_explicit_explanation_not_fabricated_starts(self):
        self.respond(self.create_cycle(), self.a3, 'Yes', '', '2026-09-20')
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['undated'], 1)
        self.assertEqual(response.context['employed'], 2)
        self.assertEqual(response.context['total_hired'], 1)
        self.assertContains(response, 'no valid current-job start date')
        self.assertContains(response, 'Missing dates are never guessed')
        self.assertEqual(response.context['period_totals'], [1, 0, 0, 0])

    def test_zero_dated_starts_displays_explanation_instead_of_empty_chart(self):
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), {
            **self.params(), 'period': 'monthly', 'year': 2026, 'month': 6
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_hired'], 0)
        self.assertContains(response, 'No dated current-job starts to plot')
        self.assertNotContains(response, '<canvas id="employabilityQuarterChart"', html=False)
        self.assertEqual(response.context['employed'], 2)

    def test_respondent_share_uses_respondent_count_not_employment_count(self):
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), self.params())
        self.assertEqual(response.status_code, 200)
        college_cit = next(row for row in response.context['display_rows'] if row.get('college') == 'CIT')
        self.assertEqual(college_cit['employed'], 0)
        self.assertEqual(college_cit['university_share'], 33.33)
        self.assertEqual(response.context['respondent_share_display'], '100.00%')
        csv = self.get_over_https(reverse('surveys:employability_report'), {**self.params(), 'format': 'csv'})
        last_row = csv.content.decode('utf-8').splitlines()[-1]
        self.assertTrue(last_row.endswith('100.00%'), last_row)

    def test_no_respondents_shows_na_rate_and_share(self):
        self.client.force_login(self.admin)
        response = self.get_over_https(reverse('surveys:employability_report'), {
            **self.params(), 'cohort_year': 2030
        })
        self.assertEqual(response.context['respondent_share_display'], 'N/A')
        self.assertEqual(response.context['rate_display'], 'N/A')
