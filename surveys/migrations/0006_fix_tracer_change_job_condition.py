import json

from django.db import migrations


ALUMNI_TITLE = "NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)"


def fix_change_job_condition(apps, schema_editor):
    Survey = apps.get_model("surveys", "Survey")

    for survey in Survey.objects.filter(title=ALUMNI_TITLE):
        by_key = {}
        for question in survey.questions.all():
            try:
                meta = json.loads(question.help_text or "{}")
            except json.JSONDecodeError:
                continue
            key = meta.get("key")
            if key:
                by_key[key] = (question, meta)

        required = ("p3_employed", "p3_first_job", "p3_reasons_change")
        if not all(key in by_key for key in required):
            continue

        employed, _ = by_key["p3_employed"]
        first_job, _ = by_key["p3_first_job"]
        change_reasons, meta = by_key["p3_reasons_change"]
        show_when = {
            str(employed.id): ["yes"],
            str(first_job.id): ["no"],
        }
        if meta.get("show_when") == show_when:
            continue

        meta["show_when"] = show_when
        change_reasons.help_text = json.dumps(meta)
        change_reasons.save(update_fields=["help_text"])


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0005_employerresponseanswer"),
    ]

    operations = [
        migrations.RunPython(fix_change_job_condition, migrations.RunPython.noop),
    ]
