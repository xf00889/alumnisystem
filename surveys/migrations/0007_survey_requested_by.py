from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0006_fix_tracer_change_job_condition"),
    ]

    operations = [
        migrations.AddField(
            model_name="survey",
            name="requested_by",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
