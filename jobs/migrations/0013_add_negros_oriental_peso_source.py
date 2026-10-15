from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('jobs', '0012_jobposting_updated_at_userjobaiscore')]

    operations = [
        migrations.AlterField(
            model_name='scrapedjob', name='source',
            field=models.CharField(
                max_length=20, default='BOSSJOB',
                choices=[
                    ('BOSSJOB','BossJob.ph'),('JOBSTREET','JobStreet Philippines'),
                    ('LINKEDIN','LinkedIn'),('INDEED','Indeed Philippines'),
                    ('KALIBRR','Kalibrr'),('PHILJOBNET','PhilJobNet (DOLE)'),
                    ('PESO_NEGROS_ORIENTAL','Negros Oriental PESO (vacancy leads)'),
                    ('ONLINEJOBS','OnlineJobs.ph'),('JORA','Jora Philippines'),
                    ('MYNIMO','Mynimo'),('WORKABROAD','WorkAbroad.ph'),('OTHER','Other'),
                ],
            ),
        ),
    ]
