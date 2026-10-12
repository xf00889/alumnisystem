from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_imported_alumni(apps, schema_editor):
    Alumni = apps.get_model('alumni_directory', 'Alumni')
    GraduateRegistry = apps.get_model('alumni_directory', 'GraduateRegistry')

    for alumni in Alumni.objects.filter(user__is_active=False).select_related('user').iterator():
        first_name = alumni.user.first_name.strip()
        last_name = alumni.user.last_name.strip()
        if not first_name or not last_name:
            continue
        GraduateRegistry.objects.get_or_create(
            first_name=first_name.split()[0],
            last_name=last_name,
            campus=alumni.campus,
            graduation_year=alumni.graduation_year,
            course=alumni.course,
            defaults={'email': alumni.user.email},
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('alumni_directory', '0008_fix_bsit_course_codes'),
    ]

    operations = [
        migrations.CreateModel(
            name='GraduateRegistry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('campus', models.CharField(choices=[('MAIN', 'Dumaguete Main Campus'), ('BAIS1', 'Bais City Campus I'), ('BAIS2', 'Bais City Campus II'), ('BSC', 'Bayawan-Sta. Catalina Campus'), ('SIATON', 'Siaton Campus'), ('GUI', 'Guihulngan Campus'), ('PAM', 'Pamplona Campus'), ('MAB', 'Mabinay Campus')], default='BSC', max_length=10)),
                ('graduation_year', models.IntegerField()),
                ('course', models.CharField(blank=True, max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('imported_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('claimed_by', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='graduate_registry_record', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Graduate registry',
                'ordering': ['-graduation_year', 'last_name', 'first_name'],
                'indexes': [models.Index(fields=['last_name', 'first_name', 'graduation_year', 'campus'], name='alumni_dire_last_na_3e94d8_idx')],
            },
        ),
        migrations.RunPython(copy_imported_alumni, migrations.RunPython.noop),
    ]
