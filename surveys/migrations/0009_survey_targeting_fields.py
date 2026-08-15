from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0008_survey_display_to_all_survey_target_college"),
    ]

    operations = [
        migrations.AddField(
            model_name="survey",
            name="target_campus",
            field=models.CharField(
                blank=True,
                choices=[
                    ("MAIN", "Dumaguete Main Campus"),
                    ("BAIS1", "Bais City Campus I"),
                    ("BAIS2", "Bais City Campus II"),
                    ("BSC", "Bayawan-Sta. Catalina Campus"),
                    ("SIATON", "Siaton Campus"),
                    ("GUI", "Guihulngan Campus"),
                    ("PAM", "Pamplona Campus"),
                    ("MAB", "Mabinay Campus"),
                ],
                default="",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="survey",
            name="target_program",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="survey",
            name="target_graduation_year_from",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="survey",
            name="target_graduation_year_to",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
