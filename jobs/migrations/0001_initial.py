# Generated by Django 4.2.19 on 2025-03-09 23:02

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobPosting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=250, unique=True)),
                ('company_name', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=200)),
                ('job_type', models.CharField(choices=[('FULL_TIME', 'Full Time'), ('PART_TIME', 'Part Time'), ('CONTRACT', 'Contract'), ('REMOTE', 'Remote'), ('INTERNSHIP', 'Internship')], default='FULL_TIME', max_length=20)),
                ('job_description', models.TextField()),
                ('requirements', models.TextField(blank=True, help_text='List the job requirements and qualifications')),
                ('responsibilities', models.TextField(blank=True, help_text='List the key job responsibilities')),
                ('experience_level', models.CharField(choices=[('ENTRY', 'Entry Level'), ('MID', 'Mid Level'), ('SENIOR', 'Senior Level'), ('EXECUTIVE', 'Executive Level')], default='ENTRY', max_length=20)),
                ('skills_required', models.TextField(blank=True, help_text='List required skills (comma-separated)')),
                ('education_requirements', models.TextField(blank=True, help_text='Specify education requirements')),
                ('benefits', models.TextField(blank=True, help_text='List job benefits and perks')),
                ('application_link', models.URLField(blank=True, max_length=500, null=True, validators=[django.core.validators.URLValidator()])),
                ('salary_range', models.CharField(blank=True, max_length=100, null=True)),
                ('posted_date', models.DateTimeField(auto_now_add=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('source', models.CharField(choices=[('manual', 'Manual'), ('indeed', 'Indeed')], default='manual', max_length=50)),
                ('source_type', models.CharField(choices=[('INTERNAL', 'NORSU Internal'), ('EXTERNAL', 'External Organization')], default='EXTERNAL', max_length=20)),
                ('external_id', models.CharField(blank=True, max_length=100, null=True)),
                ('last_scraped', models.DateTimeField(blank=True, null=True)),
                ('accepts_internal_applications', models.BooleanField(default=False, help_text='Allow applications through the system')),
                ('posted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_postings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-posted_date'],
            },
        ),
        migrations.CreateModel(
            name='RequiredDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('document_type', models.CharField(choices=[('RESUME', 'Resume/CV'), ('COVER_LETTER', 'Cover Letter'), ('TRANSCRIPT', 'Transcript of Records'), ('DIPLOMA', 'Diploma'), ('CERTIFICATION', 'Certification'), ('PORTFOLIO', 'Portfolio'), ('RECOMMENDATION', 'Recommendation Letter'), ('GOVERNMENT_ID', 'Government ID'), ('OTHER', 'Other Document')], max_length=20)),
                ('description', models.TextField(blank=True, help_text='Additional instructions or requirements for this document')),
                ('is_required', models.BooleanField(default=True)),
                ('file_types', models.CharField(default='.pdf,.doc,.docx', help_text='Comma-separated list of allowed file extensions', max_length=200)),
                ('max_file_size', models.IntegerField(default=5242880, help_text='Maximum file size in bytes')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='required_documents', to='jobs.jobposting')),
            ],
            options={
                'ordering': ['document_type'],
            },
        ),
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Review'), ('SHORTLISTED', 'Shortlisted'), ('INTERVIEWED', 'Interviewed'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('cover_letter', models.TextField(blank=True, null=True)),
                ('resume', models.FileField(upload_to='job_applications/resumes/')),
                ('additional_documents', models.FileField(blank=True, null=True, upload_to='job_applications/documents/')),
                ('notes', models.TextField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_applications', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='jobs.jobposting')),
            ],
            options={
                'ordering': ['-application_date'],
            },
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['job_type'], name='jobs_jobpos_job_typ_fa6fc4_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['posted_date'], name='jobs_jobpos_posted__2014b9_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['is_featured'], name='jobs_jobpos_is_feat_3126c5_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['source_type'], name='jobs_jobpos_source__7a2f04_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='jobapplication',
            unique_together={('job', 'applicant')},
        ),
    ]
