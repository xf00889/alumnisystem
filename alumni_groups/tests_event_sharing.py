"""Event notify-groups form flows and group-admin sharing authorization."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from core.models.notifications import Notification
from events.models import Event
from .models import AlumniGroup, GroupMembership, GroupEventShareRequest, GroupNotification, Post


class EventGroupReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.staff = U.objects.create_user(username='event_publisher', password='testpass', is_staff=True)
        cls.group_admin = U.objects.create_user(username='group_reviewer', password='testpass')
        cls.co_admin = U.objects.create_user(username='another_group_admin', password='testpass')
        cls.member = U.objects.create_user(username='group_regular', password='testpass')
        cls.outsider = U.objects.create_user(username='unrelated_group_admin', password='testpass')
        cls.group = AlumniGroup.objects.create(name='Event Team 2026', description='test', group_type='MANUAL', created_by=cls.staff)
        cls.other_group = AlumniGroup.objects.create(name='Separate Group 2026', description='test', group_type='MANUAL', created_by=cls.staff)
        for user,role,group in [
            (cls.group_admin,'ADMIN',cls.group), (cls.co_admin,'ADMIN',cls.group),
            (cls.member,'MEMBER',cls.group), (cls.outsider,'ADMIN',cls.other_group),
        ]:
            GroupMembership.objects.create(group=group, user=user, role=role, status='APPROVED', is_active=True)

    def event(self,status='published'):
        return Event.objects.create(title='University Reunion', description='<p>Welcome!</p><script>alert(1)</script>',
            start_date=timezone.now()+timedelta(days=3), end_date=timezone.now()+timedelta(days=3,hours=2),
            location='NORSU Main',status=status,created_by=self.staff, visibility='public')

    def action(self,share,who='group_admin',action='share'):
        self.client.force_login(getattr(self,who))
        return self.client.post(reverse('alumni_groups:handle_event_share',kwargs={'share_id':share.pk}),{'action':action})

    def test_published_selection_notifies_only_active_admins(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event, group=self.group)
        self.assertEqual(share.status,'PENDING')
        self.assertEqual(Post.objects.count(),0)
        self.assertEqual(set(GroupNotification.objects.filter(event_share_request=share).values_list('recipient_id',flat=True)),{self.group_admin.pk,self.co_admin.pk})
        self.assertEqual(Notification.objects.filter(object_id=share.pk,content_type=ContentType.objects.get_for_model(share)).count(),2)
        event.notified_groups.add(self.group)
        self.assertEqual(GroupEventShareRequest.objects.count(),1)
        self.assertEqual(GroupNotification.objects.count(),2)
        self.assertEqual(Notification.objects.count(),2)

    def test_draft_no_notification_until_published(self):
        event=self.event('draft')
        event.notified_groups.add(self.group)
        self.assertEqual(GroupEventShareRequest.objects.count(),0)
        event.status='published'
        event.save(update_fields=['status'])
        self.assertEqual(GroupEventShareRequest.objects.count(),1)

    def test_deselection_withdraws_pending_and_prevents_post(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        event.notified_groups.remove(self.group)
        share.refresh_from_db()
        self.assertEqual(share.status,'WITHDRAWN')
        self.assertEqual(self.action(share).status_code,400)
        self.assertEqual(Post.objects.count(),0)

    def test_clear_and_cancellation_remove_pending(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        event.notified_groups.clear()
        share.refresh_from_db()
        self.assertEqual(share.status,'WITHDRAWN')
        event.notified_groups.add(self.group)
        share.refresh_from_db()
        self.assertEqual(share.status,'PENDING')
        event.status='cancelled'
        event.save(update_fields=['status'])
        share.refresh_from_db()
        self.assertEqual(share.status,'WITHDRAWN')
        self.assertEqual(self.action(share).status_code,400)

    def test_admin_can_share_once_and_link_source(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.assertEqual(self.action(share).status_code,302)
        share.refresh_from_db()
        self.assertEqual(share.status,'SHARED')
        self.assertEqual(share.handled_by,self.group_admin)
        self.assertEqual(share.post.status,'APPROVED')
        self.assertFalse(share.post.is_pinned)
        self.assertIn('University Reunion',share.post.content)
        self.assertNotIn('<script>',share.post.content)
        self.assertEqual(self.action(share,who='co_admin',action='pin').status_code,302)
        self.assertEqual(Post.objects.count(),1)
        self.assertEqual(GroupNotification.objects.filter(event_share_request=share,is_read=False).count(),0)
        self.assertEqual(Notification.objects.filter(is_read=False).count(),0)

    def test_share_and_pin(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.assertEqual(self.action(share,action='pin').status_code,302)
        share.refresh_from_db()
        self.assertEqual(share.status,'PINNED')
        self.assertTrue(share.post.is_pinned)

    def test_dismiss_without_post(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.assertEqual(self.action(share,action='dismiss').status_code,302)
        share.refresh_from_db()
        self.assertEqual(share.status,'DISMISSED')
        self.assertEqual(Post.objects.count(),0)

    def test_nonadmins_blocked_including_other_group_admin(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        for user in ('member','outsider','staff'):
            self.assertEqual(self.action(share,who=user).status_code,403)
        self.assertEqual(Post.objects.count(),0)

    def test_no_get_and_invalid_action(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.client.force_login(self.group_admin)
        url=reverse('alumni_groups:handle_event_share',kwargs={'share_id':share.pk})
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url,{'action':'delete'}).status_code,400)
        self.assertEqual(Post.objects.count(),0)

    def test_group_inbox_shows_admin_requests_and_links(self):
        event=self.event()
        event.notified_groups.add(self.group)
        self.client.force_login(self.group_admin)
        response=self.client.get(reverse('alumni_groups:group_detail', kwargs={'slug':self.group.slug})+'?tab=notifications')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Share & pin')
        self.assertContains(response,'University Reunion')
        self.client.force_login(self.member)
        response=self.client.get(reverse('alumni_groups:group_detail', kwargs={'slug':self.group.slug}))
        self.assertNotContains(response,'Share & pin')
        self.assertNotContains(response,'Events awaiting your review')

    def test_form_selector_scope(self):
        from events.forms import EventForm, PublicEventForm
        self.other_group.is_active=False
        self.other_group.save(update_fields=['is_active'])
        self.assertIn(self.group,list(EventForm().fields['notified_groups'].queryset))
        self.assertNotIn(self.other_group,list(PublicEventForm().fields['notified_groups'].queryset))

    def test_staff_member_cannot_bypass_group_admin_review(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.member.is_staff=True
        self.member.save(update_fields=['is_staff'])
        self.assertEqual(self.action(share,who='member').status_code,403)
        self.client.force_login(self.member)
        page=self.client.get(reverse('alumni_groups:group_detail',kwargs={'slug':self.group.slug}))
        self.assertNotContains(page,'Share & pin')

    def test_expired_event_not_shareable(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        event.end_date=timezone.now()-timedelta(days=1)
        event.save(update_fields=['end_date'])
        self.assertEqual(self.action(share).status_code,400)
        self.assertEqual(Post.objects.count(),0)

    def test_cancel_after_sharing_unpublishes_promoted_post(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.assertEqual(self.action(share,action='pin').status_code,302)
        share.refresh_from_db()
        promoted=share.post
        event.status='cancelled'
        event.save(update_fields=['status'])
        share.refresh_from_db()
        promoted.refresh_from_db()
        self.assertEqual(share.status,'WITHDRAWN')
        self.assertIsNone(share.post_id)
        self.assertEqual(promoted.status,'REJECTED')
        self.assertFalse(promoted.is_pinned)
        self.assertEqual(self.action(share,action='pin').status_code,400)
        self.assertFalse(Post.objects.filter(pk=promoted.pk,status='APPROVED').exists())

    def test_deselection_after_sharing_unpublishes_post_and_allows_reselect(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.assertEqual(self.action(share,action='share').status_code,302)
        share.refresh_from_db()
        old_post_id=share.post_id
        event.notified_groups.remove(self.group)
        share.refresh_from_db()
        self.assertEqual(share.status,'WITHDRAWN')
        self.assertEqual(Post.objects.get(pk=old_post_id).status,'REJECTED')
        event.notified_groups.add(self.group)
        share.refresh_from_db()
        self.assertEqual(share.status,'PENDING')
        self.assertEqual(self.action(share,action='share').status_code,302)
        share.refresh_from_db()
        self.assertNotEqual(share.post_id,old_post_id)
        self.assertEqual(Post.objects.filter(status='APPROVED').count(),1)

    def test_deleting_event_retracts_shared_post_and_cleans_notice(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.assertEqual(self.action(share,action='pin').status_code,302)
        share.refresh_from_db()
        post_id=share.post_id
        share_id=share.pk
        ct=ContentType.objects.get_for_model(share)
        event.delete()
        self.assertFalse(GroupEventShareRequest.objects.filter(pk=share_id).exists())
        self.assertEqual(Post.objects.get(pk=post_id).status,'REJECTED')
        self.assertFalse(Notification.objects.filter(content_type=ct,object_id=share_id).exists())

    def test_reselected_group_restores_pending_notice(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        self.action(share,action='invalid')  # invalid action leaves pending
        event.notified_groups.remove(self.group)
        event.notified_groups.add(self.group)
        share.refresh_from_db()
        self.assertEqual(share.status,'PENDING')
        self.assertEqual(GroupNotification.objects.filter(event_share_request=share,is_read=False).count(),2)
        self.assertEqual(Notification.objects.filter(
            object_id=share.pk,content_type=ContentType.objects.get_for_model(share),is_read=False
        ).count(),2)

    def posted_event(self, **overrides):
        start=(timezone.now()+timedelta(days=5)).replace(second=0,microsecond=0)
        end=start+timedelta(hours=3)
        data={
            'title':'Workshop for Graduates', 'description':'Career orientation',
            'start_date':start.strftime('%Y-%m-%dT%H:%M'),
            'end_date':end.strftime('%Y-%m-%dT%H:%M'),
            'location':'Main Campus Hall', 'visibility':'public',
            'status':'published', 'notified_groups':[str(self.group.pk)],
        }
        data.update(overrides)
        return data

    def test_staff_event_create_and_update_form_group_selection(self):
        self.client.force_login(self.staff)
        response=self.client.post(reverse('events:event_create'),self.posted_event())
        self.assertEqual(response.status_code,302, getattr(response,'content',b'')[:400])
        event=Event.objects.get(title='Workshop for Graduates')
        self.assertTrue(event.notified_groups.filter(pk=self.group.pk).exists())
        share=GroupEventShareRequest.objects.get(event=event,group=self.group)
        self.assertEqual(share.status,'PENDING')
        response=self.client.post(reverse('events:event_update',kwargs={'pk':event.pk}),
                                  self.posted_event(notified_groups=[],title='Revised Workshop'))
        self.assertEqual(response.status_code,302)
        share.refresh_from_db()
        self.assertEqual(share.status,'WITHDRAWN')

    def test_public_event_form_queues_group_review(self):
        self.client.force_login(self.staff)
        data=self.posted_event()
        data.pop('status')
        response=self.client.post(reverse('events:create_public_event'),data)
        self.assertEqual(response.status_code,302, getattr(response,'content',b'')[:400])
        event=Event.objects.get(title='Workshop for Graduates')
        self.assertEqual(event.status,'published')
        self.assertTrue(GroupEventShareRequest.objects.filter(event=event,group=self.group,status='PENDING').exists())

    def test_cross_site_csrf_enforced(self):
        event=self.event()
        event.notified_groups.add(self.group)
        share=GroupEventShareRequest.objects.get(event=event)
        from django.test import Client
        strict=Client(enforce_csrf_checks=True)
        strict.force_login(self.group_admin)
        response=strict.post(reverse('alumni_groups:handle_event_share',kwargs={'share_id':share.pk}),{'action':'pin'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(Post.objects.count(),0)
