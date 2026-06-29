import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from surveys.management.commands.seed_tracer_study import ALUMNI_TITLE
from surveys.models import Survey


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
