from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0009_survey_targeting_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="survey",
            name="show_on_public_page",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "List this alumni questionnaire on the public tracer-study page. "
                    "Employer questionnaires are public automatically."
                ),
            ),
        ),
    ]
