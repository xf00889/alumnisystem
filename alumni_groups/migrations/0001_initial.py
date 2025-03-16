from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AlumniGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('description', models.TextField()),
                ('group_type', models.CharField(choices=[('AUTO', 'Automatic'), ('MANUAL', 'Manual'), ('HYBRID', 'Hybrid')], max_length=10)),
                ('visibility', models.CharField(choices=[('PUBLIC', 'Public'), ('PRIVATE', 'Private'), ('RESTRICTED', 'Restricted')], default='PUBLIC', max_length=10)),
                ('batch_start_year', models.IntegerField(blank=True, null=True)),
                ('batch_end_year', models.IntegerField(blank=True, null=True)),
                ('course', models.CharField(blank=True, max_length=100)),
                ('campus', models.CharField(choices=[('MAIN', 'NORSU Main Campus'), ('GUIHULNGAN', 'NORSU Guihulngan Campus'), ('SIATON', 'NORSU Siaton Campus'), ('PAMPLONA', 'NORSU Pamplona Campus'), ('BAIS', 'NORSU Bais Campus'), ('BSC', 'NORSU BSC (Bayawan-Sta. Catalina) Campus')], default='MAIN', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('requires_approval', models.BooleanField(default=False)),
                ('has_security_questions', models.BooleanField(default=False)),
                ('require_post_approval', models.BooleanField(default=True)),
                ('max_members', models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1)])),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_groups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('MEMBER', 'Member'), ('MODERATOR', 'Moderator'), ('ADMIN', 'Admin')], default='MEMBER', max_length=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('BLOCKED', 'Blocked')], default='PENDING', max_length=10)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_active_at', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='alumni_groups.alumnigroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('group', 'user')},
            },
        ),
    ] 