from io import StringIO
from unittest.mock import patch
from bs4 import BeautifulSoup

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from cms.models import LegalPage


class LegalPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_legal_pages', stdout=StringIO())
        user_model = get_user_model()
        cls.staff = user_model.objects.create_user(
            username='legal-staff', email='legal-staff@example.com',
            password='test-password', is_staff=True,
        )
        cls.member = user_model.objects.create_user(
            username='legal-member', email='legal-member@example.com',
            password='test-password',
        )

    def setUp(self):
        setup_patcher = patch(
            'setup.middleware.SetupRequiredMiddleware._is_setup_complete',
            return_value=True,
        )
        setup_patcher.start()
        self.addCleanup(setup_patcher.stop)

    def test_seed_is_idempotent_and_preserves_admin_edits(self):
        self.assertEqual(LegalPage.objects.count(), 4)
        terms = LegalPage.objects.get(page_type='terms')
        terms.title = 'Updated Terms'
        terms.save()

        call_command('seed_legal_pages', stdout=StringIO())

        self.assertEqual(LegalPage.objects.count(), 4)
        terms.refresh_from_db()
        self.assertEqual(terms.title, 'Updated Terms')

    def test_published_page_is_public_and_sanitized(self):
        terms = LegalPage.objects.get(page_type='terms')
        terms.content = '## Safe heading\n\n<script>alert(1)</script>\n\n[unsafe](javascript:alert(1))'
        terms.save()

        response = self.client.get(reverse('core:legal_page', args=['terms']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Safe heading</h2>', html=True)
        page = BeautifulSoup(response.content, 'html.parser')
        legal_content = page.select_one('.legal-content')
        self.assertIsNone(legal_content.find('script'))
        self.assertNotIn('javascript:', str(legal_content))
        self.assertEqual(page.select_one('.legal-page-header h1').get_text(strip=True), 'Terms of Use')
        self.assertEqual(page.select_one('.legal-nav [aria-current="page"]').get_text(strip=True), 'Terms of Use')

        footer_legal = page.select_one('.footer-legal')
        self.assertEqual(
            [link.get_text(strip=True) for link in footer_legal.select('a')],
            list(LegalPage.objects.values_list('title', flat=True)),
        )
        self.assertIsNone(page.select_one('.footer-bottom nav[aria-label="Legal"]'))

    def test_hidden_page_returns_404(self):
        LegalPage.objects.filter(page_type='terms').update(is_published=False)
        response = self.client.get(reverse('core:legal_page', args=['terms']))
        self.assertEqual(response.status_code, 404)

    def test_auth_page_links_to_dynamic_terms_and_privacy_pages(self):
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('core:legal_page', args=['terms']))
        self.assertContains(response, reverse('core:legal_page', args=['privacy']))

    def test_only_staff_can_manage_legal_pages(self):
        list_url = reverse('cms:legal_page_list')
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(list_url).status_code, 403)

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(list_url).status_code, 200)

        terms = LegalPage.objects.get(page_type='terms')
        response = self.client.post(reverse('cms:legal_page_edit', args=[terms.pk]), {
            'title': 'Admin-edited Terms',
            'summary': terms.summary,
            'content': terms.content,
            'effective_date': terms.effective_date.isoformat(),
            'is_published': 'on',
            'order': terms.order,
        })
        self.assertRedirects(response, list_url)
        terms.refresh_from_db()
        self.assertEqual(terms.title, 'Admin-edited Terms')
