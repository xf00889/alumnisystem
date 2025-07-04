# Generated by Django 5.0.2 on 2025-06-10 01:42

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='hash_signature',
            field=models.CharField(blank=True, help_text='Hash signature based on job content for deduplication', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='search_location',
            field=models.CharField(blank=True, help_text='Location used to find this job', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='search_query',
            field=models.CharField(blank=True, help_text='Search query used to find this job', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='title_normalized',
            field=models.CharField(blank=True, help_text='Normalized version of job title for deduplication', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='jobposting',
            name='source',
            field=models.CharField(choices=[('manual', 'Manual'), ('indeed', 'Indeed'), ('bossjobs', 'BossJobs')], default='manual', max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='jobposting',
            unique_together={('source', 'external_id')},
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['source'], name='jobs_jobpos_source_9226ee_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['external_id'], name='jobs_jobpos_externa_2a3141_idx'),
        ),
    ]
