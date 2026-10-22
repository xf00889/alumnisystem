"""Guard Graduate Registry URL names used by the admin sidebar and import workflow."""
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from alumni_directory import registry_views


class GraduateRegistryRoutingTests(SimpleTestCase):
    def test_registry_page_route(self):
        url = reverse('alumni_directory:graduate_registry')
        self.assertEqual(url, '/alumni/registry/')
        self.assertIs(resolve(url).func, registry_views.graduate_registry)

    def test_registry_compare_route(self):
        url = reverse('alumni_directory:registry_compare')
        self.assertEqual(url, '/alumni/registry/compare/')
        self.assertIs(resolve(url).func, registry_views.registry_compare)

    def test_registry_import_route(self):
        url = reverse('alumni_directory:registry_import')
        self.assertEqual(url, '/alumni/registry/import/')
        self.assertIs(resolve(url).func, registry_views.registry_import)
