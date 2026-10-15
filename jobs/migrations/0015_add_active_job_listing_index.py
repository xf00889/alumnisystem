from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('jobs', '0014_retire_external_vacancy_source')]

    operations = [
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['is_active', '-posted_date'], name='jobs_active_date_idx'),
        ),
    ]
