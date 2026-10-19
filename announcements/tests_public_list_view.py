"""Regression checks for public announcement list filtering and rendering.

Run only with Django's isolated test database:
    python manage.py test announcements.tests_public_list_view
"""

from django.test import TestCase
from django.urls import reverse

from .models import Announcement, Category


class PublicAnnouncementListRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name='University News', slug='university-news'
        )
        cls.other_category = Category.objects.create(
            name='Career News', slug='career-news'
        )
        cls.public = Announcement.objects.create(
            title='Alumni Homecoming Notice',
            content='Public announcement for all alumni',
            target_audience='ALL',
            priority_level='LOW',
            category=cls.category,
            is_active=True,
        )
        cls.other_public = Announcement.objects.create(
            title='Campus Careers Update',
            content='Public career information',
            target_audience='ALL',
            priority_level='HIGH',
            category=cls.other_category,
            is_active=True,
        )
        cls.targeted = Announcement.objects.create(
            title='Private Alumni Batch Notice',
            content='For the specified graduation batch only',
            target_audience='BATCH',
            target_value='2025',
            is_active=True,
        )
        cls.inactive = Announcement.objects.create(
            title='Inactive Alumni News',
            content='Not yet visible',
            target_audience='ALL',
            is_active=False,
        )
        cls.url = reverse('announcements:public-announcement-list')

    def test_public_index_renders_without_attribute_error_and_hides_private_items(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public.title)
        self.assertContains(response, self.other_public.title)
        self.assertNotContains(response, self.targeted.title)
        self.assertNotContains(response, self.inactive.title)

    def test_public_search_renders_and_filters(self):
        response = self.client.get(self.url, {'q': 'Homecoming'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public.title)
        self.assertNotContains(response, self.other_public.title)
        self.assertNotContains(response, self.targeted.title)

    def test_public_category_filter_still_applies(self):
        response = self.client.get(self.url, {'category': str(self.category.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public.title)
        self.assertNotContains(response, self.other_public.title)

    def test_public_priority_query_is_not_an_admin_filter(self):
        response = self.client.get(self.url, {'priority': 'HIGH'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public.title)
        self.assertContains(response, self.other_public.title)

    def test_public_ajax_list_renders(self):
        response = self.client.get(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(self.public.title, data['html'])
        self.assertNotIn(self.targeted.title, data['html'])
