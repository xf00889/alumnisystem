"""Admin-only group summary/status and notification behavior."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from core.models import Notification
from .models import AlumniGroup, GroupMembership


class AdministrationGroupAvailabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user(username='availability_staff', password='test', is_staff=True)
        cls.member = User.objects.create_user(username='availability_member', password='test')
        cls.other = User.objects.create_user(username='availability_other', password='test')
        cls.group = AlumniGroup.objects.create(
            name='Administration Availability Test', description='Details for managers',
            group_type='MANUAL', created_by=cls.staff
        )
        GroupMembership.objects.create(group=cls.group, user=cls.member, status='APPROVED', role='MEMBER')

    @property
    def status_url(self):
        return reverse('alumni_groups:set_group_availability', kwargs={'slug': self.group.slug})

    @property
    def group_url(self):
        return reverse('alumni_groups:group_detail', kwargs={'slug': self.group.slug})

    def test_non_admin_cannot_disable_group(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(self.status_url, {'action':'disable', 'reason':'A valid administrative reason'}).status_code, 403)
        self.group.refresh_from_db()
        self.assertTrue(self.group.is_active)

    def test_reason_required_and_method_restricted(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.status_url).status_code, 405)
        self.assertEqual(self.client.post(self.status_url, {'action':'disable', 'reason':'Short'}).status_code, 400)
        self.group.refresh_from_db()
        self.assertTrue(self.group.is_active)

    def test_disable_hides_group_and_notifies_members_once(self):
        self.client.force_login(self.staff)
        reason = 'This group is disabled while administrators review its operations.'
        response = self.client.post(self.status_url, {'action':'disable', 'reason':reason})
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db()
        self.assertFalse(self.group.is_active)
        self.assertEqual(self.group.disabled_reason, reason)
        self.assertIsNotNone(self.group.disabled_at)
        notice = Notification.objects.get(recipient=self.member, notification_type='system')
        self.assertIn(reason, notice.message)
        self.client.post(self.status_url, {'action':'disable', 'reason':reason})
        self.assertEqual(Notification.objects.filter(recipient=self.member).count(), 1)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.group_url).status_code, 404)
        listing = self.client.get(reverse('alumni_groups:group_list'))
        self.assertNotContains(listing, self.group.name)
        self.client.force_login(self.staff)
        listing = self.client.get(reverse('alumni_groups:group_list'))
        self.assertContains(listing, self.group.name)
        self.assertContains(listing, 'adminGroupSummaryModal')
        self.assertContains(listing, 'adminGroupStatusModal')

    def test_enable_restores_visibility_without_losing_membership(self):
        self.client.force_login(self.staff)
        self.client.post(self.status_url, {'action':'disable', 'reason':'Paused for compliance verification.'})
        self.assertEqual(self.client.post(self.status_url, {'action':'enable'}).status_code, 302)
        self.group.refresh_from_db()
        self.assertTrue(self.group.is_active)
        self.assertEqual(self.group.disabled_reason, '')
        self.assertTrue(GroupMembership.objects.filter(group=self.group, user=self.member, status='APPROVED').exists())
        self.client.force_login(self.member)
        self.assertContains(self.client.get(reverse('alumni_groups:group_list')), self.group.name)

    def test_staff_cannot_join_group_even_by_direct_post(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('alumni_groups:join_group', kwargs={'slug': self.group.slug})).status_code, 403)
        self.assertFalse(GroupMembership.objects.filter(group=self.group, user=self.staff).exists())
