from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from surveys.models import Report, Survey
from surveys.tracer_metadata import ALUMNI_TITLE, EMPLOYER_TITLE


@override_settings(MIDDLEWARE=[
    middleware
    for middleware in settings.MIDDLEWARE
    if middleware != "setup.middleware.SetupRequiredMiddleware"
])
class SurveyAdminPresentationTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            "survey-layout-admin",
            "survey-layout-admin@example.com",
            "pass",
            is_staff=True,
        )
        self.now = timezone.now()
        self.client.force_login(self.admin)

    def make_survey(self, title, description="Survey used for admin regression tests."):
        return Survey.objects.create(
            title=title,
            description=description,
            created_by=self.admin,
            start_date=self.now,
            end_date=self.now + timedelta(days=30),
            status="active",
        )

    def test_sidebar_cards_keep_their_intrinsic_height(self):
        survey = self.make_survey("Survey layout regression")

        response = self.client.get(
            reverse("surveys:survey_detail", args=[survey.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "height: auto;")
        self.assertNotContains(response, "height: 100%;")

    def test_generic_management_list_hides_tracer_studies(self):
        regular = self.make_survey("Regular alumni survey")
        alumni_tracer = self.make_survey(
            ALUMNI_TITLE,
            "SY 2026–2027 — Alumni tracer questionnaire",
        )
        employer_tracer = self.make_survey(
            EMPLOYER_TITLE,
            "SY 2026–2027 — Employer tracer questionnaire",
        )

        response = self.client.get(reverse("surveys:survey_list"))

        self.assertEqual(response.status_code, 200)
        listed_ids = {survey.pk for survey in response.context["surveys"]}
        analytics_ids = {
            survey_data["id"] for survey_data in response.context["survey_data"]
        }
        self.assertEqual(listed_ids, {regular.pk})
        self.assertEqual(analytics_ids, {regular.pk})
        self.assertNotIn(alumni_tracer.pk, listed_ids)
        self.assertNotIn(employer_tracer.pk, listed_ids)
        self.assertContains(response, regular.title)
        self.assertNotContains(response, ALUMNI_TITLE)
        self.assertNotContains(response, EMPLOYER_TITLE)

        tracer_response = self.client.get(
            reverse("surveys:tracer_study_reports")
        )
        tracer_ids = {
            item["survey"].pk for item in tracer_response.context["surveys"]
        }
        self.assertEqual(tracer_response.status_code, 200)
        self.assertIn(alumni_tracer.pk, tracer_ids)
        self.assertIn(employer_tracer.pk, tracer_ids)

    def test_report_type_badge_and_export_action_are_readable_and_aligned(self):
        report = Report.objects.create(
            title="Feedback",
            description="Feedback Report",
            report_type="feedback",
            parameters={},
            created_by=self.admin,
        )

        response = self.client.get(
            reverse("surveys:report_detail", args=[report.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="badge badge-primary"')
        self.assertContains(response, ".info-item .badge-primary")
        self.assertContains(response, "color: var(--text-light);")
        self.assertContains(
            response,
            'class="card-header report-results-header"',
        )
        self.assertContains(response, ".report-results-header")
        self.assertContains(response, "width: 100%;")

    def test_tracer_report_list_wraps_without_horizontal_scrolling(self):
        self.make_survey(
            ALUMNI_TITLE,
            "SY 2025–2026 — Alumni tracer questionnaire",
        )

        response = self.client.get(reverse("surveys:tracer_study_reports"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-label="Visibility"')
        self.assertContains(response, 'data-label="Study Period"')
        self.assertContains(response, "table-layout: fixed;")
        self.assertContains(
            response,
            "grid-template-columns: repeat(2, minmax(0, 1fr));",
        )
        self.assertNotContains(response, "min-width: 1080px;")

    def test_report_modal_removes_only_the_duplicate_body_export(self):
        report = Report.objects.create(
            title="Tracer Study Report",
            description="Tracer report modal regression test",
            report_type="feedback",
            parameters={},
            created_by=self.admin,
        )

        detail_response = self.client.get(
            reverse("surveys:report_detail", args=[report.pk])
        )
        list_response = self.client.get(reverse("surveys:report_list"))

        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "report-results-export")
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(
            list_response,
            "cardClone.querySelectorAll('.report-results-export')",
        )
        self.assertContains(
            list_response,
            '/surveys/admin/reports/${reportId}/export-pdf/',
        )

    def test_tracer_form_part_headers_use_white_text(self):
        response = self.client.get(reverse("surveys:tracer_study_reports"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "#tracer-study-form .tracer-part-header h3 span",
        )
        self.assertContains(response, "color: var(--text-light);")
