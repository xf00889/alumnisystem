from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('jobs', '0015_add_active_job_listing_index')]

    operations = [
        migrations.CreateModel(
            name='JobApplicationDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('file', models.FileField(upload_to='job_applications/requirements/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='required_document_files', to='jobs.jobapplication',
                )),
                ('requirement', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='submitted_files', to='jobs.requireddocument',
                )),
            ],
            options={'ordering': ['pk']},
        ),
    ]
