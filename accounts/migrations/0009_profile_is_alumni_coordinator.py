# Generated migration for adding is_alumni_coordinator field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_profile_is_hr'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_alumni_coordinator',
            field=models.BooleanField(default=False, help_text='Designates whether this user is an Alumni Coordinator with admin access but no system configuration permissions'),
        ),
    ]
