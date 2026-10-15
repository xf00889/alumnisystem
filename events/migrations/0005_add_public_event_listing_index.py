from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('events', '0004_remove_maybe_rsvp_option')]

    operations = [
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['status', 'start_date'], name='events_status_start_idx'),
        ),
    ]
