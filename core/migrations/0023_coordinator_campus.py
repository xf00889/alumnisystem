from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0022_alter_aiconfig_model_name'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='CoordinatorCampus', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('campus', models.CharField(max_length=10)), ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coordinator_campus_assignments', to=settings.AUTH_USER_MODEL))], options={'ordering': ['campus']}),
        migrations.AddConstraint(model_name='coordinatorcampus', constraint=models.UniqueConstraint(fields=('user','campus'), name='coordinator_unique_campus')),
    ]
