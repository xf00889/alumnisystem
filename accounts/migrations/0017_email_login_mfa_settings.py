from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0016_profile_extended_alumni_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailLoginMFASettings',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('enabled', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_login_mfa', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Email sign-in verification settings', 'verbose_name_plural': 'Email sign-in verification settings'},
        ),
    ]
