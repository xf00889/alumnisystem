"""Community actions and access invariants; uses Django's dedicated test database."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import (
    AlumniGroup, GroupMembership, Post, PostBookmark, PostReport, GroupPoll,
    GroupPollVote, GroupEvent, GroupEventRSVP, GroupDiscussion,
    GroupDiscussionComment, GroupNotification, Comment,
)


class GroupCommunityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username='community_admin', password='test', is_staff=True)
        cls.alumni = User.objects.create_user(username='community_alumni', password='test')
        cls.other = User.objects.create_user(username='community_other', password='test')
        cls.guest = User.objects.create_user(username='community_guest', password='test')
        cls.group = AlumniGroup.objects.create(name='Community Test Group', description='test', group_type='MANUAL', visibility='PRIVATE', created_by=cls.admin)
        cls.other_group = AlumniGroup.objects.create(name='Other Private Group', description='test', group_type='MANUAL', visibility='PRIVATE', created_by=cls.admin)
        for user, role in [(cls.admin,'ADMIN'),(cls.alumni,'MEMBER'),(cls.other,'MEMBER')]:
            GroupMembership.objects.create(group=cls.group, user=user, role=role, status='APPROVED')
        cls.post = Post.objects.create(group=cls.group, author=cls.admin, content='Public approved for members', status='APPROVED')
        cls.pending = Post.objects.create(group=cls.group, author=cls.alumni, content='Pending private', status='PENDING')

    def url(self, name, **kwargs):
        return reverse('alumni_groups:'+name, kwargs=kwargs)

    def test_bookmark_toggle_saved_feed(self):
        self.client.force_login(self.alumni)
        u=self.url('toggle_bookmark',post_id=self.post.pk)
        self.assertEqual(self.client.post(u).status_code,302)
        self.assertEqual(PostBookmark.objects.count(),1)
        self.assertContains(self.client.get(self.url('group_detail',slug=self.group.slug),{'feed_sort':'saved'}),'Public approved for members')
        self.client.post(u)
        self.assertEqual(PostBookmark.objects.count(),0)

    def test_bookmark_pending_and_outsider_denied(self):
        self.client.force_login(self.guest)
        self.assertEqual(self.client.post(self.url('toggle_bookmark',post_id=self.post.pk)).status_code,403)
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(self.url('toggle_bookmark',post_id=self.pending.pk)).status_code,404)

    def test_post_pin_admin_only_and_visibility(self):
        url=self.url('pin_post',post_id=self.post.pk)
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(url).status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url).status_code,302)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_pinned)

    def test_post_report_review(self):
        self.client.force_login(self.alumni)
        url=self.url('report_post',post_id=self.post.pk)
        self.assertEqual(self.client.post(url,{'reason':'Offensive content'}).status_code,302)
        self.client.post(url,{'reason':'Repeat report'})
        self.assertEqual(PostReport.objects.count(),1)
        report=PostReport.objects.get()
        self.assertEqual(self.client.post(self.url('review_report',report_id=report.pk),{'action':'resolve'}).status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url('review_report',report_id=report.pk),{'action':'resolve'}).status_code,302)
        report.refresh_from_db()
        self.assertEqual(report.status,'RESOLVED')

    def test_invalid_reports(self):
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(self.url('report_post',post_id=self.post.pk),{'reason':'x'}).status_code,400)

    def test_poll_create_vote_once(self):
        self.client.force_login(self.alumni)
        create=self.url('create_poll',slug=self.group.slug)
        self.assertEqual(self.client.post(create,{'question':'What is our next activity?', 'options':['Hike','Workshop','Hike','']}).status_code,302)
        poll=GroupPoll.objects.get()
        self.assertEqual(poll.options.count(),2)
        url=self.url('vote_poll',poll_id=poll.pk)
        self.client.post(url, {'option':poll.options.first().pk})
        self.client.post(url, {'option':poll.options.last().pk})
        self.assertEqual(GroupPollVote.objects.filter(poll=poll,voter=self.alumni).count(),1)

    def test_poll_invalid_and_outside_option(self):
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(self.url('create_poll',slug=self.group.slug),{'question':'Bad','options':['a']}).status_code,400)
        poll=GroupPoll.objects.create(group=self.group,author=self.admin,question='Which one?')
        other_poll=GroupPoll.objects.create(group=self.other_group,author=self.admin,question='Other?')
        option=other_poll.options.create(label='Nope')
        self.assertEqual(self.client.post(self.url('vote_poll',poll_id=poll.pk),{'option':option.pk}).status_code,404)
        self.client.force_login(self.guest)
        self.assertEqual(self.client.post(self.url('vote_poll',poll_id=poll.pk),{'option':option.pk}).status_code,403)

    def test_poll_list_hidden_for_guest(self):
        GroupPoll.objects.create(group=self.group,author=self.admin,question='Confidential poll')
        self.client.force_login(self.guest)
        response=self.client.get(self.url('group_detail',slug=self.group.slug))
        self.assertNotContains(response,'Confidential poll')

    def test_discussion_categories_and_threaded_reply(self):
        self.client.force_login(self.alumni)
        response=self.client.post(self.url('create_discussion',slug=self.group.slug),{'title':'Job opportunities','content':'Do you have positions?','category':'JOBS'})
        self.assertEqual(response.status_code,302)
        discussion=GroupDiscussion.objects.get()
        self.assertEqual(discussion.category,'JOBS')
        url=self.url('reply_discussion',discussion_id=discussion.pk)
        self.client.post(url,{'content':'First reply'})
        parent=GroupDiscussionComment.objects.get()
        self.client.post(url,{'content':'Nested reply','parent_id':parent.pk})
        self.assertEqual(GroupDiscussionComment.objects.exclude(parent=None).count(),1)

    def test_discussion_locked_and_cross_group_reply(self):
        discussion=GroupDiscussion.objects.create(group=self.group,created_by=self.admin,title='Locked topic',content='No replies',is_locked=True)
        url=self.url('reply_discussion',discussion_id=discussion.pk)
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(url,{'content':'No'}).status_code,403)
        self.client.force_login(self.guest)
        self.assertEqual(self.client.post(url,{'content':'No'}).status_code,403)

    def test_discussion_moderation(self):
        topic=GroupDiscussion.objects.create(group=self.group,created_by=self.admin,title='topic',content='content')
        url=self.url('moderate_discussion',discussion_id=topic.pk)
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(url,{'action':'lock'}).status_code,403)
        self.client.force_login(self.admin)
        self.client.post(url,{'action':'lock'})
        topic.refresh_from_db()
        self.assertTrue(topic.is_locked)

    def test_event_rsvp_capacity(self):
        event=GroupEvent.objects.create(group=self.group,title='Event',description='Reunion',start_date=timezone.now()+timedelta(days=1),end_date=timezone.now()+timedelta(days=1,hours=2),address='Campus',created_by=self.admin,max_participants=1)
        url=self.url('rsvp_event',event_id=event.pk)
        self.client.force_login(self.alumni)
        self.client.post(url,{'response':'GOING'})
        self.client.force_login(self.other)
        self.client.post(url,{'response':'GOING'})
        self.assertEqual(GroupEventRSVP.objects.filter(event=event,response='GOING').count(),1)
        self.client.post(url,{'response':'MAYBE'})
        self.assertEqual(GroupEventRSVP.objects.count(),2)

    def test_event_rsvp_nonmember_denied(self):
        event=GroupEvent.objects.create(group=self.group,title='Event',description='Reunion',start_date=timezone.now(),end_date=timezone.now(),address='Campus',created_by=self.admin)
        self.client.force_login(self.guest)
        self.assertEqual(self.client.post(self.url('rsvp_event',event_id=event.pk),{'response':'GOING'}).status_code,403)

    def test_mention_notification_owner_only(self):
        self.client.force_login(self.admin)
        response=self.client.post(self.url('create_discussion',slug=self.group.slug),{'title':'Hello everyone','content':'Hello @community_alumni, see you!','category':'GENERAL'})
        self.assertEqual(response.status_code,302)
        notice=GroupNotification.objects.get(recipient=self.alumni)
        url=self.url('mark_notification_read',notification_id=notice.pk)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url).status_code,404)
        self.client.force_login(self.alumni)
        self.client.post(url)
        notice.refresh_from_db()
        self.assertTrue(notice.is_read)

    def test_post_comment_reply_and_limit(self):
        self.client.force_login(self.alumni)
        u=self.url('add_comment',post_id=self.post.pk)
        self.assertEqual(self.client.post(u,{'content':'x'*3001}).status_code,400)
        self.client.post(u,{'content':'Reply to post'})
        parent=Comment.objects.get()
        self.client.post(u,{'content':'@community_other, I agree', 'parent_id':parent.pk})
        self.assertEqual(Comment.objects.filter(parent=parent).count(),1)
        self.assertTrue(GroupNotification.objects.filter(recipient=self.other).exists())

    def test_member_role_and_last_admin_guards(self):
        self.client.force_login(self.admin)
        membership=GroupMembership.objects.get(group=self.group,user=self.alumni)
        url=self.url('update_member_status',membership_id=membership.pk)
        self.assertEqual(self.client.post(url,content_type='application/json', data='{"action":"make_moderator"}').status_code,200)
        membership.refresh_from_db()
        self.assertEqual(membership.role,'MODERATOR')
        self.client.post(url,content_type='application/json', data='{"action":"demote"}')
        membership.refresh_from_db()
        self.assertEqual(membership.role,'MEMBER')
        mymembership=GroupMembership.objects.get(group=self.group,user=self.admin)
        self.assertEqual(self.client.post(self.url('update_member_status',membership_id=mymembership.pk),content_type='application/json',data='{"action":"remove"}').status_code,400)

    def test_membership_search(self):
        self.client.force_login(self.admin)
        response=self.client.get(self.url('manage_members',slug=self.group.slug),{'member_search':'community_alumni'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(list(response.context['active_members'].values_list('user__username',flat=True)),['community_alumni'])

    def test_moderation_approval_notification(self):
        self.client.force_login(self.admin)
        response=self.client.post(self.url('approve_post',post_id=self.pending.pk),{'action':'approve'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(GroupNotification.objects.filter(recipient=self.alumni,post=self.pending).exists())

    def test_actions_require_post(self):
        self.client.force_login(self.admin)
        for url in [self.url('pin_post',post_id=self.post.pk),self.url('create_poll',slug=self.group.slug)]:
            self.assertEqual(self.client.get(url).status_code,405)

    def test_group_event_creation_admin_only_and_validation(self):
        url=self.url('create_group_event',slug=self.group.slug)
        payload={'title':'Career reunion','description':'Meet new graduates','start_date':'2026-11-10T09:00','end_date':'2026-11-10T11:00','address':'Online', 'is_online':'on','meeting_link':'https://example.org/meeting'}
        self.client.force_login(self.alumni)
        self.assertEqual(self.client.post(url,payload).status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url,payload).status_code,302)
        self.assertEqual(GroupEvent.objects.filter(group=self.group,title='Career reunion').count(),1)

    def test_report_removal_hides_post(self):
        self.client.force_login(self.alumni)
        self.client.post(self.url('report_post',post_id=self.post.pk),{'reason':'Off topic commercial content'})
        report=PostReport.objects.get()
        self.client.force_login(self.admin)
        self.client.post(self.url('review_report',report_id=report.pk),{'action':'remove_post'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.status,'REJECTED')

    def test_poll_and_discussions_show_in_member_template(self):
        poll=GroupPoll.objects.create(group=self.group,author=self.admin,question='Community question')
        poll.options.create(label='Yes')
        poll.options.create(label='No')
        GroupDiscussion.objects.create(group=self.group,created_by=self.admin,title='Mentoring',content='Looking for mentors',category='MENTORSHIP')
        self.client.force_login(self.alumni)
        response=self.client.get(self.url('group_detail',slug=self.group.slug),{'tab':'polls'})
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Community question')
        self.assertContains(response,'Mentoring')
