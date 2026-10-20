"""Regression tests: own-response job dates, no duplicates, historical report cutoff."""
import json
from datetime import date, timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from alumni_directory.models import Alumni
from surveys.employability_reports import _answer_map
from surveys.models import (
    QuestionOption, ResponseAnswer, Survey, SurveyQuestion,
    SurveyResponse, TracerJobStartUpdate,
)
from surveys.tracer_metadata import ALUMNI_TITLE
from surveys.tracer_study import _job_start_values, _tracer_local_today

MIDDLEWARE = [m for m in settings.MIDDLEWARE
              if m != "setup.middleware.SetupRequiredMiddleware"]


@override_settings(MIDDLEWARE=MIDDLEWARE)
class EmploymentDateUpdateTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user('tracer-admin-update', 'tracer-admin@example.com', 'password', is_staff=True)
        self.user = User.objects.create_user('tracer-update', 'tracer-update@example.com', 'password')
        self.other_user = User.objects.create_user('tracer-other', 'tracer-other@example.com', 'password')
        self.alumni = self._alumni(self.user, 2025)
        self.other_alumni = self._alumni(self.other_user, 2025)
        now = timezone.now()
        self.survey = Survey.objects.create(
            title=ALUMNI_TITLE, description='Employment details verification', created_by=self.admin,
            start_date=now-timedelta(days=30), end_date=now-timedelta(days=1),
            status='closed', display_to_all=True,
        )
        self.employed_q = SurveyQuestion.objects.create(
            survey=self.survey, question_text='Are you presently employed?', question_type='multiple_choice',
            is_required=True, display_order=1, help_text=json.dumps({'key':'p3_employed'}),
        )
        self.yes = QuestionOption.objects.create(question=self.employed_q, option_text='Yes', display_order=1)
        self.no = QuestionOption.objects.create(question=self.employed_q, option_text='No', display_order=2)
        self.date_q = SurveyQuestion.objects.create(
            survey=self.survey, question_text='Date you started your current job', question_type='date',
            is_required=False, display_order=2, help_text=json.dumps({'key':'p3_current_job_start'}),
        )
        self.response = self._response(self.alumni, self.yes)
        self.url = reverse('surveys:tracer_study_employment_date_update', args=[self.response.pk])

    def _alumni(self, user, year):
        user.profile.has_completed_registration = True
        user.profile.save(update_fields=['has_completed_registration'])
        return Alumni.objects.create(user=user, campus='BSC', college='CTE', course='BEED',
            graduation_year=year, gender='M', province='Negros Oriental', city='Bayawan', address='Address')

    def _response(self, alumni, selection):
        response = SurveyResponse.objects.create(survey=self.survey, alumni=alumni)
        ResponseAnswer.objects.create(response=response, question=self.employed_q, selected_option=selection)
        return response

    def test_requires_owner_login_and_employed_response(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'job_start_date':'2025-01-09'}).status_code, 404)
        other_response = self._response(self.other_alumni, self.no)
        self.assertEqual(self.client.get(reverse('surveys:tracer_study_employment_date_update', args=[other_response.pk])).status_code, 404)

    def test_add_date_without_duplicate_response_even_if_survey_closed(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        result = self.client.post(self.url, {'job_start_date':'2025-07-05'})
        self.assertEqual(result.status_code, 302)
        self.assertEqual(SurveyResponse.objects.filter(survey=self.survey, alumni=self.alumni).count(), 1)
        correction = TracerJobStartUpdate.objects.get(response=self.response)
        self.assertEqual(correction.start_date, date(2025, 7, 5))
        self.assertFalse(correction.date_unknown)
        self.assertFalse(self.response.answers.filter(question=self.date_q).exists())
        self.client.post(self.url, {'job_start_date':'2025-07-05'})
        self.assertEqual(self.response.job_start_updates.count(), 1)

    def test_cannot_recall_and_invalid_dates(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.url, {'unknown_date':'on'}).status_code, 302)
        self.assertEqual(_answer_map(self.response)['p3_current_job_start'], 'unknown')
        self.assertEqual(self.client.post(self.url, {}).status_code, 400)
        self.assertEqual(self.client.post(self.url, {'unknown_date':'on', 'job_start_date':'2025-03-01'}).status_code, 400)
        self.assertEqual(self.client.post(self.url, {'job_start_date':'2999-01-01'}).status_code, 400)
        self.assertEqual(self.response.job_start_updates.count(), 1)

    def test_as_of_snapshot_ignores_corrections_recorded_later(self):
        ResponseAnswer.objects.create(response=self.response, question=self.date_q, text_answer='unknown')
        self.client.force_login(self.user)
        self.client.post(self.url, {'job_start_date':'2025-06-15'})
        before = _tracer_local_today() - timedelta(days=1)
        self.assertEqual(_answer_map(self.response, as_of=before)['p3_current_job_start'], 'unknown')
        self.assertEqual(_answer_map(self.response, as_of=_tracer_local_today())['p3_current_job_start'], '2025-06-15')
        self.assertEqual(self.response.answers.get(question=self.date_q).text_answer, 'unknown')

    def test_new_submission_requires_date_or_explicit_unknown(self):
        self.survey.status = 'active'
        self.survey.end_date = timezone.now() + timedelta(days=1)
        self.survey.save(update_fields=['status', 'end_date'])
        self.client.force_login(self.other_user)
        survey_url = reverse('surveys:tracer_study_alumni')
        result = self.client.post(survey_url, {
            f'question_{self.employed_q.pk}': str(self.yes.pk),
        })
        self.assertEqual(result.status_code, 400)
        self.assertFalse(SurveyResponse.objects.filter(alumni=self.other_alumni).exists())
        result = self.client.post(survey_url, {
            f'question_{self.employed_q.pk}': str(self.yes.pk),
            'job_start_unknown': 'on',
        })
        self.assertEqual(result.status_code, 200)
        response = SurveyResponse.objects.get(alumni=self.other_alumni, survey=self.survey)
        self.assertEqual(response.answers.get(question=self.date_q).text_answer, 'unknown')

    def test_job_start_validator_requires_date_or_unknown(self):
        with self.assertRaises(ValueError):
            _job_start_values('', '')
        with self.assertRaises(ValueError):
            _job_start_values('2025-01-01', 'on')
        with self.assertRaises(ValueError):
            _job_start_values('2999-01-01', '')
        self.assertEqual(_job_start_values('', 'on'), (None, True))
        self.assertEqual(_job_start_values('2025-01-01', ''), (date(2025,1,1), False))
