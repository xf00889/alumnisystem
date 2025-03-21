# Generated by Django 4.2.19 on 2025-03-10 15:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('alumni_directory', '0001_initial'),
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievement',
            name='verification_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='achievement',
            name='verified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='questionoption',
            name='allow_custom',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='survey',
            name='external_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='survey',
            name='is_external',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='surveyquestion',
            name='help_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='surveyquestion',
            name='scale_type',
            field=models.CharField(blank=True, choices=[('1-5', '1 to 5'), ('1-10', '1 to 10'), ('a-f', 'A to F'), ('frequency', 'Frequency (Never - Always)'), ('agreement', 'Agreement (Strongly Disagree - Strongly Agree)'), ('satisfaction', 'Satisfaction (Very Unsatisfied - Very Satisfied)'), ('custom', 'Custom Scale')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='achievement_type',
            field=models.CharField(choices=[('award', 'Award/Recognition'), ('certification', 'Professional Certification'), ('publication', 'Publication'), ('speaking', 'Speaking Engagement'), ('education', 'Educational Achievement'), ('other', 'Other Achievement')], max_length=20),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='employmentrecord',
            name='alumni',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employment_records', to='alumni_directory.alumni'),
        ),
        migrations.AlterField(
            model_name='employmentrecord',
            name='company_name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='employmentrecord',
            name='industry',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='employmentrecord',
            name='job_title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='employmentrecord',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.address'),
        ),
        migrations.AlterField(
            model_name='employmentrecord',
            name='salary_range',
            field=models.CharField(blank=True, choices=[('0-50k', '$0 - $50,000'), ('50k-100k', '$50,000 - $100,000'), ('100k-150k', '$100,000 - $150,000'), ('150k-200k', '$150,000 - $200,000'), ('200k+', '$200,000+'), ('prefer_not', 'Prefer not to say')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='display_order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='option_text',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='report',
            name='report_type',
            field=models.CharField(choices=[('employment', 'Employment Trends'), ('geographic', 'Geographic Distribution'), ('achievements', 'Alumni Achievements'), ('feedback', 'Survey Feedback'), ('custom', 'Custom Report')], max_length=20),
        ),
        migrations.AlterField(
            model_name='report',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='responseanswer',
            name='rating_value',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='responseanswer',
            name='selected_option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='surveys.questionoption'),
        ),
        migrations.AlterField(
            model_name='survey',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='surveyquestion',
            name='display_order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='surveyquestion',
            name='question_type',
            field=models.CharField(choices=[('text', 'Text Answer'), ('multiple_choice', 'Multiple Choice (Single Answer)'), ('checkbox', 'Multiple Choice (Multiple Answers)'), ('rating', 'Rating Scale'), ('likert', 'Likert Scale'), ('date', 'Date'), ('time', 'Time'), ('file', 'File Upload'), ('email', 'Email'), ('number', 'Number'), ('phone', 'Phone Number'), ('url', 'Website URL')], max_length=20),
        ),
    ]
