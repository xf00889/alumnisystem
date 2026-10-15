"""Retire the experimental provincial vacancy source without deleting prior data.

0013 is kept as immutable migration history because it may already be applied
in production. 0014 restores the previous field choices and deactivates any
legacy aggregate records; their records remain stored for audit purposes.
"""
from django.db import migrations, models


RETIRED_SOURCE = 'PESO_NEGROS_ORIENTAL'


def archive_retired_records(apps, schema_editor):
    ScrapedJob = apps.get_model('jobs', 'ScrapedJob')
    ScrapedJob.objects.using(schema_editor.connection.alias).filter(
        source=RETIRED_SOURCE,
    ).update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [('jobs', '0013_add_negros_oriental_peso_source')]

    operations = [
        migrations.RunPython(archive_retired_records, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='scrapedjob',
            name='source',
            field=models.CharField(
                max_length=20,
                default='BOSSJOB',
                choices=[
                    ('BOSSJOB', 'BossJob.ph'),
                    ('JOBSTREET', 'JobStreet Philippines'),
                    ('LINKEDIN', 'LinkedIn'),
                    ('INDEED', 'Indeed Philippines'),
                    ('KALIBRR', 'Kalibrr'),
                    ('PHILJOBNET', 'PhilJobNet (DOLE)'),
                    ('ONLINEJOBS', 'OnlineJobs.ph'),
                    ('JORA', 'Jora Philippines'),
                    ('MYNIMO', 'Mynimo'),
                    ('WORKABROAD', 'WorkAbroad.ph'),
                    ('OTHER', 'Other'),
                ],
            ),
        ),
    ]
