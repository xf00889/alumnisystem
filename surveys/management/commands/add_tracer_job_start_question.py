"""Non-destructive, idempotent addition of a dated current-job-start answer.

Unlike seed_tracer_study, this command NEVER deletes survey questions/answers.
"""
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from surveys.models import Survey, SurveyQuestion
from surveys.tracer_metadata import ALUMNI_TITLE


class Command(BaseCommand):
    help = "Safely add an optional current-job start date to each alumni tracer cycle."

    @transaction.atomic
    def handle(self, *args, **options):
        surveys = Survey.objects.filter(title=ALUMNI_TITLE).order_by('pk')
        for survey in surveys:
            questions = list(survey.questions.all())
            by_key = {}
            for question in questions:
                try:
                    key = json.loads(question.help_text or '{}').get('key')
                except (TypeError, ValueError):
                    continue
                if key:
                    by_key[key] = question
            if 'p3_current_job_start' in by_key:
                self.stdout.write(f'Survey {survey.pk}: question already exists; unchanged.')
                continue
            employed = by_key.get('p3_employed')
            if employed is None:
                self.stdout.write(self.style.WARNING(f'Survey {survey.pk}: missing p3_employed; skipped.'))
                continue
            anchor = by_key.get('p3_position') or employed
            survey.questions.filter(display_order__gt=anchor.display_order).update(display_order=F('display_order') + 1)
            question = SurveyQuestion.objects.create(
                survey=survey,
                question_text='Date you started your current job (if known)',
                question_type='date', is_required=False,
                display_order=anchor.display_order + 1,
                help_text=json.dumps({
                    'key': 'p3_current_job_start',
                    'part': 'PART III - Employment Data',
                    'description': 'Enter the date you began your current job. Leave blank if unknown; this helps the Office of Alumni Affairs prepare accurate quarterly hiring statistics.',
                    'show_when': {str(employed.pk): ['yes']},
                    'multiline': False,
                }),
            )
            self.stdout.write(self.style.SUCCESS(f'Survey {survey.pk}: added question {question.pk}; existing answers preserved.'))
