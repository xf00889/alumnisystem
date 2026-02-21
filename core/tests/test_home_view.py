from django.test import TestCase, Client
from django.urls import reverse
from cms.models import SiteConfig
from unittest.mock import patch


class HomeViewHeroSectionTestCase(TestCase):
    """Test that the home view passes hero section data from CMS to the template"""

    def setUp(self):
        self.client = Client()
        self.home_url = reverse('core:home')
        # Get or create site config with hero section data
        self.site_config = SiteConfig.get_site_config()

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_home_view_returns_200(self, mock_setup):
        """Test that the home view returns a 200 status code"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_hero_headline_in_context(self, mock_setup):
        """Test that hero_headline is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('hero_headline', response.context)
        self.assertEqual(
            response.context['hero_headline'],
            self.site_config.hero_headline
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_hero_subheadline_in_context(self, mock_setup):
        """Test that hero_subheadline is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('hero_subheadline', response.context)
        self.assertEqual(
            response.context['hero_subheadline'],
            self.site_config.hero_subheadline
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_cta_primary_text_in_context(self, mock_setup):
        """Test that cta_primary_text is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('cta_primary_text', response.context)
        self.assertEqual(
            response.context['cta_primary_text'],
            self.site_config.hero_primary_cta_text
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_cta_secondary_text_in_context(self, mock_setup):
        """Test that cta_secondary_text is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('cta_secondary_text', response.context)
        self.assertEqual(
            response.context['cta_secondary_text'],
            self.site_config.hero_secondary_cta_text
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_hero_microcopy_in_context(self, mock_setup):
        """Test that hero_microcopy is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('hero_microcopy', response.context)
        self.assertEqual(
            response.context['hero_microcopy'],
            self.site_config.hero_microcopy
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_alumni_count_in_context(self, mock_setup):
        """Test that alumni_count (from CMS) is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('alumni_count', response.context)
        self.assertEqual(
            response.context['alumni_count'],
            self.site_config.hero_alumni_count
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_opportunities_count_in_context(self, mock_setup):
        """Test that opportunities_count (from CMS) is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('opportunities_count', response.context)
        self.assertEqual(
            response.context['opportunities_count'],
            self.site_config.hero_opportunities_count
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_countries_count_in_context(self, mock_setup):
        """Test that countries_count (from CMS) is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('countries_count', response.context)
        self.assertEqual(
            response.context['countries_count'],
            self.site_config.hero_countries_count
        )

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_site_config_in_context(self, mock_setup):
        """Test that site_config is passed to the template context"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        self.assertIn('site_config', response.context)
        self.assertIsNotNone(response.context['site_config'])

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_hero_section_component_rendered(self, mock_setup):
        """Test that the hero section component is rendered in the response"""
        mock_setup.return_value = True
        response = self.client.get(self.home_url)
        # Check that the hero section is rendered (contains hero-specific classes)
        self.assertContains(response, 'hero-section', status_code=200)
        self.assertContains(response, 'hero-headline', status_code=200)
        self.assertContains(response, 'hero-subheadline', status_code=200)

    @patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete')
    def test_hero_data_with_custom_cms_values(self, mock_setup):
        """Test that custom CMS values are correctly passed to the template"""
        mock_setup.return_value = True
        # Update site config with custom values
        self.site_config.hero_headline = "Test Headline"
        self.site_config.hero_subheadline = "Test Subheadline"
        self.site_config.hero_primary_cta_text = "Test CTA"
        self.site_config.hero_alumni_count = "10,000+"
        self.site_config.save()

        response = self.client.get(self.home_url)
        self.assertEqual(response.context['hero_headline'], "Test Headline")
        self.assertEqual(response.context['hero_subheadline'], "Test Subheadline")
        self.assertEqual(response.context['cta_primary_text'], "Test CTA")
        self.assertEqual(response.context['alumni_count'], "10,000+")
