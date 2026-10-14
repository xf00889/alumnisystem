from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('alumni_groups', '0007_postreport_moderation_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name='alumnigroup', name='disabled_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='alumnigroup', name='disabled_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='alumnigroup', name='disabled_by', field=models.ForeignKey(
            to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL,
            related_name='disabled_alumni_groups', null=True, blank=True)),
    ]
