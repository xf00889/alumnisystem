# Generated by Django 5.0.2 on 2025-05-23 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='experience',
            options={'ordering': ['-is_current', '-start_date'], 'verbose_name': 'Experience', 'verbose_name_plural': 'Experience'},
        ),
        migrations.AddField(
            model_name='experience',
            name='achievements',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='experience',
            name='career_significance',
            field=models.CharField(choices=[('REGULAR', 'Regular Position'), ('PROMOTION', 'Promotion'), ('LATERAL', 'Lateral Move'), ('NEW_ROLE', 'New Role'), ('COMPANY_CHANGE', 'Company Change')], default='REGULAR', max_length=20),
        ),
        migrations.AddField(
            model_name='experience',
            name='salary_range',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='experience',
            name='skills_gained',
            field=models.TextField(blank=True, help_text='Comma-separated list of skills gained in this role'),
        ),
        migrations.AlterField(
            model_name='experience',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
