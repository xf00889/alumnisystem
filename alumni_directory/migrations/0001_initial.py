# Generated by Django 4.2.19 on 2025-02-19 22:30

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alumni',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                ('alternate_email', models.EmailField(blank=True, max_length=254)),
                ('linkedin_profile', models.URLField(blank=True)),
                ('country', django_countries.fields.CountryField(default='PH', max_length=2)),
                ('province', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('college', models.CharField(choices=[('CAS', 'College of Arts and Sciences'), ('CAFF', 'College of Agriculture, Forestry and Fishery'), ('CBA', 'College of Business Administration'), ('CCJE', 'College of Criminal Justice Education'), ('CEA', 'College of Engineering and Architecture'), ('CIT', 'College of Industrial Technology'), ('CNPAHS', 'College of Nursing, Pharmacy and Allied Health Sciences'), ('CTE', 'College of Teacher Education'), ('CTHM', 'College of Tourism and Hospitality Management')], max_length=10)),
                ('campus', models.CharField(choices=[('MAIN', 'Dumaguete Main Campus'), ('NORTH', 'Dumaguete North Campus'), ('BAIS1', 'Bais City Campus I'), ('BAIS2', 'Bais City Campus II'), ('BSC', 'Bayawan-Sta. Catalina Campus'), ('SIATON', 'Siaton Campus'), ('GUI', 'Guihulngan Campus'), ('PAM', 'Pamplona Campus'), ('MAB', 'Mabinay Campus')], max_length=10)),
                ('graduation_year', models.IntegerField()),
                ('course', models.CharField(max_length=200)),
                ('major', models.CharField(blank=True, max_length=200)),
                ('honors', models.CharField(blank=True, max_length=200)),
                ('thesis_title', models.CharField(blank=True, max_length=500, null=True)),
                ('current_company', models.CharField(blank=True, max_length=200)),
                ('job_title', models.CharField(blank=True, max_length=200)),
                ('employment_status', models.CharField(blank=True, choices=[('EMPLOYED_FULL', 'Employed Full-Time'), ('EMPLOYED_PART', 'Employed Part-Time'), ('SELF_EMPLOYED', 'Self-Employed'), ('UNEMPLOYED', 'Unemployed'), ('STUDENT', 'Further Studies'), ('RETIRED', 'Retired'), ('INTERN', 'Internship/OJT')], max_length=20)),
                ('industry', models.CharField(blank=True, max_length=200)),
                ('skills', models.TextField(blank=True, help_text='Comma-separated list of skills')),
                ('interests', models.TextField(blank=True, help_text='Comma-separated list of interests')),
                ('bio', models.TextField(blank=True)),
                ('achievements', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_featured', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Alumni',
                'ordering': ['-graduation_year', 'user__last_name'],
            },
        ),
        migrations.CreateModel(
            name='CareerPath',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=255)),
                ('position', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('is_current', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('achievements', models.TextField(blank=True)),
                ('promotion_type', models.CharField(blank=True, choices=[('PROMOTION', 'Promotion'), ('LATERAL', 'Lateral Move'), ('NEW_ROLE', 'New Role'), ('COMPANY_CHANGE', 'Company Change')], max_length=20)),
                ('salary_range', models.CharField(blank=True, max_length=100)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('skills_gained', models.TextField(blank=True, help_text='Comma-separated list of skills gained in this role')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alumni', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='career_paths', to='alumni_directory.alumni')),
            ],
            options={
                'verbose_name': 'Career Path',
                'verbose_name_plural': 'Career Paths',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='AlumniDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('document_type', models.CharField(choices=[('RESUME', 'Resume/CV'), ('CERT', 'Certification'), ('DIPLOMA', 'Diploma'), ('TOR', 'Transcript of Records'), ('OTHER', 'Other')], max_length=20)),
                ('file', models.FileField(upload_to='alumni_documents/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])])),
                ('description', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('alumni', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='alumni_directory.alumni')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('achievement_type', models.CharField(choices=[('AWARD', 'Award'), ('CERTIFICATION', 'Certification'), ('PUBLICATION', 'Publication'), ('PROJECT', 'Project'), ('RECOGNITION', 'Recognition'), ('OTHER', 'Other')], max_length=20)),
                ('date_achieved', models.DateField()),
                ('description', models.TextField(blank=True)),
                ('issuer', models.CharField(blank=True, max_length=255)),
                ('url', models.URLField(blank=True)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='achievements/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alumni', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements_list', to='alumni_directory.alumni')),
            ],
            options={
                'verbose_name': 'Achievement',
                'verbose_name_plural': 'Achievements',
                'ordering': ['-date_achieved'],
            },
        ),
        migrations.AddIndex(
            model_name='alumni',
            index=models.Index(fields=['graduation_year', 'course'], name='alumni_dire_graduat_d32c0e_idx'),
        ),
        migrations.AddIndex(
            model_name='alumni',
            index=models.Index(fields=['province', 'city'], name='alumni_dire_provinc_1f8edb_idx'),
        ),
        migrations.AddIndex(
            model_name='alumni',
            index=models.Index(fields=['college', 'campus'], name='alumni_dire_college_b08d1c_idx'),
        ),
    ]
