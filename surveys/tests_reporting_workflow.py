"""Regression checks for separated survey and tracer report flows."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from alumni_directory.models import Alumni
from surveys.models import Report, ResponseAnswer, Survey, SurveyQuestion, SurveyResponse
from surveys.tracer_metadata import ALUMNI_TITLE
from surveys.views import ReportDetailView, SurveyListView
from django.conf import settings


@override_settings(MIDDLEWARE=[m for m in settings.MIDDLEWARE if m != 'setup.middleware.SetupRequiredMiddleware'])
class ReportingWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user('report-admin', 'admin@localhost.test', 'pass', is_staff=True)
        user = get_user_model().objects.create_user('respondent', 'respondent@localhost.test', 'pass')
        cls.alumni = Alumni.objects.create(
            user=user, campus='BSC', college='CAS', course='BSINT',
            graduation_year=2024, gender='M', province='Negros Oriental',
            city='Dumaguete', address='Sample address',
        )
        now = timezone.now()
        values = dict(description='Academic year cycle', created_by=cls.admin,
                      start_date=now - timedelta(days=1), end_date=now + timedelta(days=7), status='active')
        cls.tracer = Survey.objects.create(title=ALUMNI_TITLE, **values)
        cls.general = Survey.objects.create(title='Graduate satisfaction', **values)
        for survey in [cls.tracer, cls.general]:
            question = SurveyQuestion.objects.create(survey=survey, question_text='Experience', question_type='text', display_order=0)
            response = SurveyResponse.objects.create(survey=survey, alumni=cls.alumni)
            ResponseAnswer.objects.create(response=response, question=question, text_answer='Private answer')

    def test_tracer_report_summary_has_no_named_text_feedback(self):
        report = Report.objects.create(title='Tracer summary', description='', report_type='feedback', created_by=self.admin, parameters={'survey_id': self.tracer.pk})
        data = ReportDetailView().generate_report_data(report)
        self.assertTrue(data['is_tracer_report'])
        self.assertEqual(data['table_data'], [])
        self.assertEqual(data['summary']['total_responses'], 1)

    def test_general_feedback_report_retains_text_responses(self):
        report = Report.objects.create(title='General survey feedback', description='', report_type='feedback', created_by=self.admin, parameters={'survey_id': self.general.pk})
        data = ReportDetailView().generate_report_data(report)
        self.assertFalse(data['is_tracer_report'])
        self.assertEqual(len(data['table_data']), 1)
        self.assertEqual(data['table_data'][0]['answer'], 'Private answer')

    def test_general_survey_dashboard_does_not_count_tracer(self):
        from django.test import RequestFactory
        request = RequestFactory().get('/surveys/admin/surveys/')
        request.user = self.admin
        view = SurveyListView()
        view.setup(request)
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        self.assertEqual(len(context['surveys']), 1)
        self.assertEqual(context['alumni_with_responses'], 1)
        self.assertEqual(context['active_surveys'], 1)
        self.assertEqual(context['college_data'][0]['count'], 1)
        # Remove the general response to ensure tracer-only activity doesn't fabricate a chart.
        SurveyResponse.objects.filter(survey=self.general).delete()
        context = view.get_context_data()
        self.assertEqual(context['alumni_with_responses'], 0)
        self.assertEqual(context['college_data'], [])
        self.assertEqual(len(context['batch_data']), 0)
