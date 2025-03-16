# Generated by Django 4.2.19 on 2025-03-09 23:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('alumni_groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('JOIN', 'Member Joined'), ('LEAVE', 'Member Left'), ('POST', 'New Post'), ('EVENT', 'New Event'), ('COMMENT', 'New Comment'), ('UPDATE', 'Group Updated')], max_length=10)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Group Activities',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_members', models.PositiveIntegerField(default=0)),
                ('active_members', models.PositiveIntegerField(default=0)),
                ('total_posts', models.PositiveIntegerField(default=0)),
                ('total_events', models.PositiveIntegerField(default=0)),
                ('total_comments', models.PositiveIntegerField(default=0)),
                ('engagement_rate', models.FloatField(default=0.0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Group Analytics',
            },
        ),
        migrations.CreateModel(
            name='GroupDiscussion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_pinned', models.BooleanField(default=False)),
                ('is_locked', models.BooleanField(default=False)),
                ('views_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='GroupDiscussionComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('address', models.CharField(max_length=255)),
                ('is_online', models.BooleanField(default=False)),
                ('meeting_link', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('max_participants', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='group_files/%Y/%m/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True)),
                ('download_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='GroupMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SecurityQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=255)),
                ('is_required', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SecurityQuestionAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_correct', models.BooleanField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='alumnigroup',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='group_covers/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='alumnigroup',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddIndex(
            model_name='alumnigroup',
            index=models.Index(fields=['name', 'group_type', 'visibility'], name='alumni_grou_name_7eca69_idx'),
        ),
        migrations.AddIndex(
            model_name='alumnigroup',
            index=models.Index(fields=['batch_start_year', 'batch_end_year'], name='alumni_grou_batch_s_c8736c_idx'),
        ),
        migrations.AddIndex(
            model_name='alumnigroup',
            index=models.Index(fields=['course', 'campus'], name='alumni_grou_course_be91eb_idx'),
        ),
        migrations.AddIndex(
            model_name='groupmembership',
            index=models.Index(fields=['group', 'user', 'role', 'status'], name='alumni_grou_group_i_10f212_idx'),
        ),
        migrations.AddField(
            model_name='securityquestionanswer',
            name='membership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_answers', to='alumni_groups.groupmembership'),
        ),
        migrations.AddField(
            model_name='securityquestionanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='alumni_groups.securityquestion'),
        ),
        migrations.AddField(
            model_name='securityquestionanswer',
            name='reviewed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_answers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='securityquestion',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_questions', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='postlike',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alumni_groups.post'),
        ),
        migrations.AddField(
            model_name='postlike',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='post',
            name='likes',
            field=models.ManyToManyField(related_name='liked_posts', through='alumni_groups.PostLike', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupmessage',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='groupmessage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupfile',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='groupfile',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupevent',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupevent',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='groupdiscussioncomment',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupdiscussioncomment',
            name='discussion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='alumni_groups.groupdiscussion'),
        ),
        migrations.AddField(
            model_name='groupdiscussioncomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='alumni_groups.groupdiscussioncomment'),
        ),
        migrations.AddField(
            model_name='groupdiscussion',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupdiscussion',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discussions', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='groupanalytics',
            name='group',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='groupactivity',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='alumni_groups.alumnigroup'),
        ),
        migrations.AddField(
            model_name='groupactivity',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='alumni_groups.post'),
        ),
        migrations.AlterUniqueTogether(
            name='postlike',
            unique_together={('post', 'user')},
        ),
    ]
