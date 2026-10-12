"""Focused group-feed regression coverage (SQLite-compatible Django TestCase)."""
from io import BytesIO
from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from .models import AlumniGroup, GroupMembership, GroupEvent, Post, PostLike


class GroupExperienceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username='groupadmin', password='test-password', is_staff=True)
        cls.member = User.objects.create_user(username='groupmember', password='test-password')
        cls.outsider = User.objects.create_user(username='outsider', password='test-password')
        cls.group = AlumniGroup.objects.create(
            name='NORSU Group Test', description='<script>alert(1)</script> & friends',
            group_type='MANUAL', visibility='PRIVATE', course='BSIT',
            require_post_approval=True, created_by=cls.admin,
        )
        GroupMembership.objects.create(group=cls.group, user=cls.admin, status='APPROVED', role='ADMIN')
        GroupMembership.objects.create(group=cls.group, user=cls.member, status='APPROVED', role='MEMBER')

    def post_url(self):
        return reverse('alumni_groups:create_post', kwargs={'slug': self.group.slug})

    def detail_url(self):
        return reverse('alumni_groups:group_detail', kwargs={'slug': self.group.slug})

    def test_ordinary_member_requires_approval_when_setting_on(self):
        self.client.force_login(self.member)
        response = self.client.post(self.post_url(), {'content': 'My first update'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'PENDING')
        self.assertEqual(Post.objects.get().status, 'PENDING')

    def test_ordinary_member_auto_approved_when_setting_off(self):
        self.group.require_post_approval = False
        self.group.save(update_fields=['require_post_approval'])
        self.client.force_login(self.member)
        response = self.client.post(self.post_url(), {'content': 'My second update'})
        self.assertEqual(response.json()['status'], 'APPROVED')

    def test_admin_post_auto_approved(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.post_url(), {'content': 'Moderator update'}).json()['status'], 'APPROVED')

    def test_nonmember_cannot_create_post(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(self.post_url(), {'content': 'No access'}).status_code, 403)

    def test_empty_content_and_image_rejected(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(self.post_url(), {'content': ' \n '}).status_code, 400)
        self.assertEqual(Post.objects.count(), 0)

    def test_invalid_photo_is_rejected(self):
        self.client.force_login(self.member)
        file = SimpleUploadedFile('bad.jpg', b'not actually an image', content_type='image/jpeg')
        self.assertEqual(self.client.post(self.post_url(), {'image': file}).status_code, 400)

    def test_photo_only_post_accepted(self):
        self.client.force_login(self.member)
        stream = BytesIO()
        Image.new('RGB', (12, 12), '#f1c96c').save(stream, format='PNG')
        photo = SimpleUploadedFile('alumni-photo.png', stream.getvalue(), content_type='image/png')
        with TemporaryDirectory() as media_dir, self.settings(MEDIA_ROOT=media_dir):
            response = self.client.post(self.post_url(), {'image': photo})
            self.assertEqual(response.status_code, 200, response.content[:500])
            self.assertTrue(Post.objects.get().image.name)

    def test_only_approved_posts_are_in_member_feed(self):
        approved = Post.objects.create(group=self.group, author=self.admin, content='Published', status='APPROVED')
        pending = Post.objects.create(group=self.group, author=self.admin, content='Private pending', status='PENDING')
        self.client.force_login(self.member)
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p.pk for p in response.context['group_posts']], [approved.pk])
        self.assertNotIn(pending.pk, [p.pk for p in response.context['group_posts']])
        self.assertNotContains(response, 'Private pending')
        self.assertContains(response, 'id="feed-tab"')

    def test_admin_sees_pending_moderation_queue(self):
        post = Post.objects.create(group=self.group, author=self.member, content='Needs approval', status='PENDING')
        self.client.force_login(self.admin)
        response = self.client.get(self.detail_url())
        self.assertContains(response, 'Needs approval')
        self.assertEqual(response.context['pending_posts'][0].pk, post.pk)

    def test_member_sees_only_own_pending_status(self):
        Post.objects.create(group=self.group, author=self.member, content='My pending', status='PENDING')
        Post.objects.create(group=self.group, author=self.admin, content='Someone else pending', status='PENDING')
        self.client.force_login(self.member)
        response = self.client.get(self.detail_url())
        self.assertContains(response, 'My pending')
        self.assertNotContains(response, 'Someone else pending')

    def test_group_events_use_correct_fields(self):
        from django.utils import timezone
        event = GroupEvent.objects.create(
            group=self.group, title='Reunion', description='Our reunion',
            start_date=timezone.now(), end_date=timezone.now(),
            address='Dumaguete City', is_active=True, created_by=self.admin,
        )
        self.client.force_login(self.member)
        response = self.client.get(self.detail_url())
        self.assertContains(response, 'Dumaguete City')
        self.assertContains(response, 'Reunion')

    def test_group_description_is_escaped(self):
        self.client.force_login(self.member)
        response = self.client.get(self.detail_url())
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_pending_post_cannot_be_liked_or_commented(self):
        post = Post.objects.create(group=self.group, author=self.member, content='Pending', status='PENDING')
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(reverse('alumni_groups:like_post', kwargs={'post_id': post.pk})).status_code, 404)
        self.assertEqual(self.client.post(reverse('alumni_groups:add_comment', kwargs={'post_id': post.pk}), {'content':'hello'}).status_code, 404)

    def test_feed_sort_by_popularity(self):
        popular = Post.objects.create(group=self.group, author=self.admin, content='Popular', status='APPROVED')
        recent = Post.objects.create(group=self.group, author=self.admin, content='Other', status='APPROVED')
        PostLike.objects.create(post=popular, user=self.member)
        self.client.force_login(self.member)
        response = self.client.get(self.detail_url(), {'feed_sort': 'popular'})
        self.assertEqual([p.pk for p in response.context['group_posts']], [popular.pk, recent.pk])
