"""Group timeline refresh must reuse the original access, filtering and ordering rules."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import AlumniGroup, GroupMembership, Post, PostBookmark, PostLike


class GroupTimelineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.manager = User.objects.create_user(username='timeline_manager', password='test', is_staff=True)
        cls.member = User.objects.create_user(username='timeline_member', password='test')
        cls.outsider = User.objects.create_user(username='timeline_outsider', password='test')
        cls.group = AlumniGroup.objects.create(
            name='Timeline Group', description='Community', group_type='MANUAL',
            visibility='PRIVATE', created_by=cls.manager,
        )
        cls.other = AlumniGroup.objects.create(
            name='Other Timeline Group', description='Other', group_type='MANUAL',
            visibility='PRIVATE', created_by=cls.manager,
        )
        cls.membership = GroupMembership.objects.create(
            user=cls.member, group=cls.group, role='MEMBER', status='APPROVED',
        )
        GroupMembership.objects.create(
            user=cls.manager, group=cls.group, role='ADMIN', status='APPROVED',
        )
        cls.first = Post.objects.create(group=cls.group, author=cls.manager, content='First authorized', status='APPROVED')
        cls.second = Post.objects.create(group=cls.group, author=cls.member, content='Latest authorized', status='APPROVED')
        cls.pending = Post.objects.create(group=cls.group, author=cls.member, content='Secret pending', status='PENDING')
        cls.rejected = Post.objects.create(group=cls.group, author=cls.manager, content='Rejected private', status='REJECTED')
        cls.other_post = Post.objects.create(group=cls.other, author=cls.manager, content='Different group secret', status='APPROVED')

    def url(self):
        return reverse('alumni_groups:feed_snapshot', kwargs={'slug': self.group.slug})

    def test_requires_group_membership(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse('alumni_groups:feed_snapshot', kwargs={'slug': self.other.slug})).status_code, 403)

    def test_requires_login(self):
        self.assertEqual(self.client.get(self.url()).status_code, 302)

    def test_inactive_membership_cannot_refresh(self):
        self.membership.is_active = False
        self.membership.save(update_fields=['is_active'])
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_only_approved_posts_rendered_as_safe_html(self):
        self.client.force_login(self.member)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['post_ids'], [self.second.id, self.first.id])
        self.assertIn('Latest authorized', result['html'])
        self.assertNotIn('Secret pending', result['html'])
        self.assertNotIn('Rejected private', result['html'])
        self.assertNotIn('Different group secret', result['html'])
        self.assertEqual(response['Cache-Control'], 'no-store, private')
        Post.objects.create(group=self.group, author=self.manager, content='<script>alert(1)</script>', status='APPROVED')
        html = self.client.get(self.url()).json()['html']
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)

    def test_new_post_appears_on_next_refresh(self):
        self.client.force_login(self.member)
        before = self.client.get(self.url()).json()['post_ids']
        new = Post.objects.create(group=self.group, author=self.manager, content='New arrival', status='APPROVED')
        after = self.client.get(self.url()).json()['post_ids']
        self.assertNotIn(new.id, before)
        self.assertEqual(after[0], new.id)

    def test_ordering_matches_visible_page_and_saved_filter(self):
        self.client.force_login(self.member)
        page = self.client.get(reverse('alumni_groups:group_detail', kwargs={'slug':self.group.slug}))
        self.assertEqual([post.id for post in page.context['group_posts']], self.client.get(self.url()).json()['post_ids'])
        PostLike.objects.create(post=self.first, user=self.member)
        self.assertEqual(self.client.get(self.url(), {'feed_sort':'popular'}).json()['post_ids'][0], self.first.id)
        self.assertEqual(self.client.get(self.url(), {'feed_sort':'oldest'}).json()['post_ids'][0], self.first.id)
        PostBookmark.objects.create(post=self.first, user=self.member)
        self.assertEqual(self.client.get(self.url(), {'feed_sort':'saved'}).json()['post_ids'], [self.first.id])
        saved_page = self.client.get(reverse('alumni_groups:group_detail', kwargs={'slug':self.group.slug}), {'feed_sort':'saved'})
        self.assertEqual([post.id for post in saved_page.context['group_posts']], [self.first.id])

    def test_pinned_post_rises_to_top_after_refresh(self):
        self.first.is_pinned = True
        self.first.save(update_fields=['is_pinned'])
        self.client.force_login(self.member)
        payload = self.client.get(self.url()).json()
        self.assertEqual(payload['post_ids'][0], self.first.id)
        self.assertIn('Pinned announcement', payload['html'])

    def test_existing_event_related_template_renders_on_refresh(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url())
        self.assertIn('post-%d' % self.first.pk, response.json()['html'])
        self.assertIn('comment-toggle', response.json()['html'])

    def test_composer_and_posts_are_in_one_feed_workspace(self):
        """The composer, heading and posts must remain in one feed workspace."""
        self.client.force_login(self.member)
        response = self.client.get(reverse('alumni_groups:group_detail', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        scroll_start = html.index('id="groupFeedScroll"')
        composer = html.index('id="postForm"')
        heading = html.index('Community feed', composer)
        posts = html.index('id="groupFeedPosts"')
        scroll_end = html.index('<!-- /.group-feed-scroll -->', scroll_start)
        self.assertLess(scroll_start, composer)
        self.assertLess(composer, heading)
        self.assertLess(heading, posts)
        self.assertLess(posts, scroll_end)

    def test_only_scrolling_refresh_action_is_rendered(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('alumni_groups:group_detail', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertNotIn('id="groupFeedRefresh"', html)
        self.assertEqual(html.count('id="groupFeedScrollRefresh"'), 1)
        self.assertIn('aria-controls="groupFeedPosts" hidden', html)
        self.assertIn('id="groupFeedRefreshStatus"', html)
