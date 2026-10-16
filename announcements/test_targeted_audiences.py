"""Run with: python manage.py test announcements.test_targeted_audiences"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from alumni_directory.models import Alumni
from .audience import announcement_recipients, normalize_target, visible_announcements_for
from .forms import AnnouncementForm
from .models import Announcement, Category


class TargetedAnnouncementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.it_user = User.objects.create_user('it_alumnus', password='pass-12345', email='it@example.org')
        cls.ed_user = User.objects.create_user('ed_alumnus', password='pass-12345', email='ed@example.org')
        cls.staff = User.objects.create_superuser('announcement_admin', 'admin@example.org', 'pass-12345')
        Alumni.objects.create(user=cls.it_user, campus='MAIN', college='CAS', graduation_year=2024, course='BSINT')
        Alumni.objects.create(user=cls.ed_user, campus='MAIN', college='CTE', graduation_year=2022, course='BSED')
        cls.category = Category.objects.create(name='Campus News', slug='campus-news')

    def make_announcement(self, audience, value=''):
        return Announcement.objects.create(
            title=f'Announcement for {audience}', content='Test message', category=self.category,
            target_audience=audience, target_value=value,
        )

    def test_college_visibility_and_recipient_selection(self):
        announcement = self.make_announcement('COLLEGE', 'CTE')
        self.assertFalse(announcement.is_visible_to(self.it_user))
        self.assertTrue(announcement.is_visible_to(self.ed_user))
        self.assertEqual(list(announcement_recipients(announcement)), [self.ed_user])
        self.assertTrue(announcement.is_visible_to(self.staff))

    def test_batch_visibility(self):
        announcement = self.make_announcement('BATCH', '2024')
        self.assertTrue(announcement.is_visible_to(self.it_user))
        self.assertFalse(announcement.is_visible_to(self.ed_user))
        self.assertEqual(list(announcement_recipients(announcement)), [self.it_user])

    def test_program_matches_stored_codes(self):
        announcement = self.make_announcement('PROGRAM', 'BSINT')
        self.assertTrue(announcement.is_visible_to(self.it_user))
        self.assertFalse(announcement.is_visible_to(self.ed_user))
        self.assertEqual(list(announcement_recipients(announcement)), [self.it_user])
        self.assertEqual(normalize_target('PROGRAM', 'Bachelor of Science in Information Technology'), 'BSINT')

    def test_list_and_modal_do_not_expose_unmatched_audience(self):
        announcement = self.make_announcement('COLLEGE', 'CTE')
        self.client.force_login(self.it_user)
        self.assertNotIn(announcement, visible_announcements_for(self.it_user))
        self.assertEqual(self.client.get(reverse('announcements:announcement-detail-api', args=[announcement.pk])).status_code, 404)

    @patch('announcements.forms.is_recaptcha_enabled', return_value=False)
    def test_target_is_required_and_normalized(self, _captcha):
        values = dict(title='Information', content='Test', category=self.category.slug,
                      priority_level='MEDIUM', target_audience='PROGRAM')
        form = AnnouncementForm(data={**values, 'target_value': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('target_value', form.errors)
        form = AnnouncementForm(data={**values, 'target_value': 'Bachelor of Science in Information Technology'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['target_value'], 'BSINT')

    @patch('announcements.forms.is_recaptcha_enabled', return_value=False)
    def test_switching_to_all_alumni_clears_previous_audience(self, _captcha):
        form = AnnouncementForm(data={
            'title': 'General', 'content': 'Welcome', 'category': self.category.slug,
            'priority_level': 'MEDIUM', 'target_audience': 'ALL', 'target_value': 'CTE',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['target_value'], '')
