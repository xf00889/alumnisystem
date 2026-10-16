from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('announcements', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='target_value',
            field=models.CharField(blank=True, default='', max_length=200,
                help_text='Batch year, college code, or degree-program code/name for a targeted announcement.'),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='target_audience',
            field=models.CharField(
                choices=[
                    ('ALL', 'All Alumni'),
                    ('RECENT', 'Recent Graduates'),
                    ('DEPARTMENT', 'Specific Department'),
                    ('BATCH', 'Graduation Batch'),
                    ('COLLEGE', 'College'),
                    ('PROGRAM', 'Degree Program'),
                ],
                default='ALL', max_length=20,
            ),
        ),
    ]
