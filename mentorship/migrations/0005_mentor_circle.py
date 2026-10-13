from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('mentorship', '0004_conversation_conversation_type_and_more'),
        ('accounts', '0015_alter_education_program'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MentorCircleMeeting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('agenda', models.TextField(blank=True)),
                ('meeting_date', models.DateTimeField()),
                ('duration', models.PositiveSmallIntegerField(default=60)),
                ('meeting_link', models.URLField(blank=True)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='circle_meetings', to='accounts.mentor')),
                ('participants', models.ManyToManyField(related_name='circle_meetings', to='accounts.mentorshiprequest')),
            ],
            options={'ordering': ['meeting_date']},
        ),
        migrations.CreateModel(
            name='MentorCircleEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('MESSAGE','Message'),('MEETING','Meeting'),('PROGRESS','Progress update'),('TIMELINE','Timeline update')], max_length=12)),
                ('title', models.CharField(blank=True, max_length=180)),
                ('body', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mentor_circle_entries', to=settings.AUTH_USER_MODEL)),
                ('meeting', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_entries', to='mentorship.mentorcirclemeeting')),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='circle_entries', to='accounts.mentor')),
                ('mentorship', models.ForeignKey(blank=True, help_text='When set, only this mentee and their mentor may read the entry.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='circle_entries', to='accounts.mentorshiprequest')),
            ],
            options={'ordering': ['created_at', 'pk']},
        ),
        migrations.AddIndex(model_name='mentorcircleentry', index=models.Index(fields=['mentor','-created_at'], name='mentor_circle_activity_idx')),
    ]
