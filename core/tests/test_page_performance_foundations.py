"""Regression guards for safe public-page caching and private-page indexing."""

from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings

from core.context_processors import seo_context, _cached_public_data


@override_settings(
    GLOBAL_TEMPLATE_CACHE_SECONDS=60,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "norsu-public-page-performance-regression-tests",
        },
    },
)
class PublicPagePerformanceTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_authenticated_pages_do_not_query_seo_configuration(self):
        request = self.factory.get('/alumni/')
        request.user = SimpleNamespace(is_authenticated=True)
        with patch('core.models.seo.PageSEO.objects.filter') as page_lookup:
            result = seo_context(request)
        self.assertTrue(result['seo']['noindex'])
        page_lookup.assert_not_called()

    def test_anonymous_account_pages_are_noindex(self):
        request = self.factory.get('/accounts/login/')
        request.user = SimpleNamespace(is_authenticated=False)
        with patch('core.models.seo.PageSEO.objects.filter') as page_lookup:
            result = seo_context(request)
        self.assertTrue(result['seo']['noindex'])
        page_lookup.assert_not_called()

    def test_shared_public_seo_is_cached_per_page_and_missing_rows(self):
        request = self.factory.get('/about-us/')
        request.user = SimpleNamespace(is_authenticated=False)
        with (patch('core.models.seo.PageSEO.objects.filter') as page_lookup,
              patch('core.models.seo.OrganizationSchema.objects.filter') as org_lookup):
            page_lookup.return_value.first.return_value = None
            org_lookup.return_value.first.return_value = None
            first = seo_context(request)
            second = seo_context(request)

        self.assertFalse(first['seo']['noindex'])
        self.assertEqual(first['seo'], second['seo'])
        page_lookup.assert_called_once()
        org_lookup.assert_called_once()

    def test_shared_public_cache_can_be_disabled_for_admin_edits(self):
        with override_settings(GLOBAL_TEMPLATE_CACHE_SECONDS=0):
            with patch('core.context_processors.cache.get_or_set') as cache_lookup:
                value = _cached_public_data('sample', lambda: 42)
        self.assertEqual(value, 42)
        cache_lookup.assert_not_called()

    def test_protected_templates_emit_robots_noindex(self):
        html = render_to_string('components/seo/seo_meta_tags.html', {
            'seo': {'noindex': True, 'title': 'Account settings'},
        })
        self.assertIn('name="robots" content="noindex, nofollow"', html)

    def test_sitemap_excludes_member_only_seo_routes(self):
        from unittest.mock import MagicMock
        from core.sitemaps import StaticPageSitemap

        queryset = MagicMock()
        queryset.exclude.return_value = queryset
        with patch('core.sitemaps.PageSEO.objects.filter', return_value=queryset):
            StaticPageSitemap().items()

        filters = [call.kwargs for call in queryset.exclude.call_args_list]
        self.assertIn({'page_path__startswith': '/accounts/'}, filters)
        self.assertIn({'page_path__startswith': '/alumni/'}, filters)
        self.assertIn({'page_path__in': ['/jobs/']}, filters)

    def test_high_traffic_indexes_exist(self):
        from jobs.models import JobPosting
        from events.models import Event
        self.assertIn('jobs_active_date_idx', [i.name for i in JobPosting._meta.indexes])
        self.assertIn('events_status_start_idx', [i.name for i in Event._meta.indexes])
