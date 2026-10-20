from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("surveys", "0010_survey_show_on_public_page")]

    operations = [
        migrations.CreateModel(
            name="TracerJobStartUpdate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField(blank=True, null=True)),
                ("date_unknown", models.BooleanField(default=False)),
                ("recorded_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("response", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_start_updates", to="surveys.surveyresponse")),
            ],
            options={"ordering": ["-recorded_at", "-pk"]},
        ),
    ]
