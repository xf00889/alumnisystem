from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alumni_groups', '0006_backfill_event_group_share_requests'),
    ]

    operations = [
        migrations.AddField(
            model_name='postreport',
            name='category',
            field=models.CharField(choices=[('SPAM', 'Spam or scam'), ('HARASSMENT', 'Harassment or hate'), ('MISINFORMATION', 'False or misleading information'), ('INAPPROPRIATE', 'Inappropriate content'), ('PRIVACY', 'Privacy or impersonation concern'), ('OTHER', 'Other concern')], default='OTHER', max_length=20),
        ),
        migrations.AddField(
            model_name='postreport',
            name='resolution_note',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='postreport',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
