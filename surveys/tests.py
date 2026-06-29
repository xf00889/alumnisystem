import json
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from alumni_directory.models import Alumni
from surveys.management.commands.seed_tracer_study import ALUMNI_TITLE
from surveys.models import Survey, SurveyResponse


class TracerStudySeedTests(TestCase):
    def test_change_job_reason_requires_employed_and_not_first_job(self):
        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )

        call_command("seed_tracer_study", verbosity=0)

        survey = Survey.objects.get(title=ALUMNI_TITLE)
        by_key = {}
        for question in survey.questions.all():
            meta = json.loads(question.help_text)
            by_key[meta["key"]] = (question, meta)

        question, meta = by_key["p3_reasons_change"]
        self.assertEqual(
            meta["show_when"],
            {
                str(by_key["p3_employed"][0].id): ["yes"],
                str(by_key["p3_first_job"][0].id): ["no"],
            },
        )
        self.assertEqual(question.question_text, "Reasons for changing jobs (select all that apply)")


@override_settings(MIDDLEWARE=[
    middleware for middleware in settings.MIDDLEWARE
    if middleware != 'setup.middleware.SetupRequiredMiddleware'
])
class TracerStudyReportResponseStatusTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user("admin", "admin@example.com", "pass", is_staff=True)
        self.respondent_user = User.objects.create_user(
            "respondent",
            "respondent@example.com",
            "pass",
            first_name="Rina",
            last_name="Responded",
        )
        self.missing_user = User.objects.create_user(
            "missing",
            "missing@example.com",
            "pass",
            first_name="Nico",
            last_name="Missing",
        )
        self.survey = Survey.objects.create(
            title=ALUMNI_TITLE,
            description="Tracer",
            created_by=self.admin,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            status="active",
        )
        self.respondent = Alumni.objects.create(
            user=self.respondent_user,
            college="CAS",
            campus="MAIN",
            graduation_year=2025,
            course="BSINT",
            gender="F",
            province="Negros Oriental",
            city="Dumaguete",
            address="A",
        )
        self.missing = Alumni.objects.create(
            user=self.missing_user,
            college="CAS",
            campus="MAIN",
            graduation_year=2026,
            course="BSCS",
            gender="M",
            province="Negros Oriental",
            city="Dumaguete",
            address="B",
        )
        SurveyResponse.objects.create(survey=self.survey, alumni=self.respondent)

    def test_report_shows_and_exports_response_status(self):
        self.client.force_login(self.admin)
        report_url = reverse("surveys:tracer_study_report", args=[self.survey.id])

        response = self.client.get(report_url)
        self.assertContains(response, "Rina Responded")
        self.assertContains(response, "Nico Missing")
        self.assertContains(response, "Export Excel")

        export = self.client.get(reverse("surveys:tracer_study_report_export", args=[self.survey.id]))
        self.assertEqual(
            export["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(export.content))
        self.assertEqual(workbook.sheetnames, ["Responded", "No Response"])
        responded_values = [cell.value for row in workbook["Responded"].iter_rows() for cell in row]
        missing_values = [cell.value for row in workbook["No Response"].iter_rows() for cell in row]
        self.assertIn("Tracer Study Response Status", responded_values)
        self.assertIn("Alumni Who Responded", responded_values)
        self.assertIn("Alumni With No Response", missing_values)
        self.assertIn("Rina Responded", responded_values)
        self.assertNotIn("Nico Missing", responded_values)
        self.assertIn("Nico Missing", missing_values)
        self.assertNotIn("Rina Responded", missing_values)
