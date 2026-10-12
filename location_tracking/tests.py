"""Focused map, sharing, privacy and geocoding regressions."""
import io
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from alumni_directory.models import Alumni
from .models import LocationData

User = get_user_model()


class LocationMapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(username='mapstaff', password='Password123', is_staff=True)
        cls.alumnus = User.objects.create_user(username='alumnus1', password='Password123', first_name='Ana', last_name='Garcia')
        cls.second = User.objects.create_user(username='alumnus2', password='Password123', first_name='Ben', last_name='Luna')
        cls.unverified = User.objects.create_user(username='unverified', password='Password123')
        cls.staff_profile = getattr(cls.staff, 'profile', None)
        for user, verified in ((cls.alumnus, True), (cls.second, True), (cls.unverified, False)):
            Alumni.objects.create(user=user, college='CAS', campus='MAIN', graduation_year=2024,
                                  course='BSCS', gender='M', province='Negros Oriental',
                                  city='Dumaguete', address='', is_verified=verified)
        cls.alumni_loc = LocationData.objects.create(user=cls.alumnus, latitude=9.310000, longitude=123.310000)
        cls.second_loc = LocationData.objects.create(user=cls.second, latitude=9.315000, longitude=123.315000)
        cls.staff_loc = LocationData.objects.create(user=cls.staff, latitude=9.320000, longitude=123.320000)
        cls.unverified_loc = LocationData.objects.create(user=cls.unverified, latitude=9.330000, longitude=123.330000)

    def setUp(self):
        setup_guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        self.addCleanup(setup_guard.stop)
        cache.clear()

    def test_map_and_feed_are_staff_only(self):
        for route in ('location_tracking:map', 'location_tracking:get_locations'):
            url = reverse(route)
            self.assertEqual(self.client.get(url).status_code, 302)
            self.client.force_login(self.alumnus)
            self.assertEqual(self.client.get(url).status_code, 302)
            self.client.force_login(self.staff)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.logout()

    def test_coordinator_can_view_map_without_becoming_alumnus(self):
        coordinator = User.objects.create_user(username='coordinator', password='Password123')
        coordinator.profile.is_alumni_coordinator = True
        coordinator.profile.save(update_fields=['is_alumni_coordinator'])
        self.client.force_login(coordinator)
        self.assertEqual(self.client.get(reverse('location_tracking:map')).status_code, 200)
        self.assertEqual(self.client.post(reverse('location_tracking:update_location'),
                                          {'latitude': 9, 'longitude': 123}).status_code, 403)

    def test_dual_role_staff_verified_alumnus_can_share(self):
        dual = User.objects.create_user(username='dualmap', password='Password123', is_staff=True)
        Alumni.objects.create(user=dual, college='CAS', campus='MAIN', graduation_year=2024,
                              course='BSCS', gender='F', province='', city='', address='', is_verified=True)
        self.client.force_login(dual)
        self.assertEqual(self.client.post(reverse('location_tracking:update_location'),
                                          {'latitude': 9, 'longitude': 123}).status_code, 200)
        locations = self.client.get(reverse('location_tracking:get_locations')).json()['locations']
        self.assertIn(dual.pk, {a['id'] for a in locations})

    def test_map_template_has_cluster_filters_and_static_assets(self):
        self.client.force_login(self.staff)
        page = self.client.get(reverse('location_tracking:map'))
        self.assertContains(page, 'groupBy')
        # Source includes isolated CSS/JS even when the simplified test base omits asset blocks.
        from django.template.loader import get_template
        source = get_template('location_tracking/map.html').template.source
        self.assertIn('alumni-location-map.js', source)
        self.assertIn('alumni-location-map.css', source)
        self.assertContains(page, 'last-shared locations')

    def test_staff_map_offers_five_basemap_styles_without_changing_cluster_controls(self):
        from django.template.loader import get_template
        self.client.force_login(self.staff)
        response = self.client.get(reverse('location_tracking:map'))
        self.assertContains(response, 'id="mapStylePicker"')
        self.assertContains(response, 'data-map-style="streets"')
        for name in ('light', 'dark', 'satellite', 'terrain'):
            self.assertContains(response, f'data-map-style="{name}"')
        self.assertContains(response, 'id="fitMap"')
        self.assertContains(response, 'id="groupBy"')
        source = get_template('location_tracking/map.html').template.source
        self.assertIn('alumni-map-basemaps.js', source)
        self.assertIn('id="mapTilerLogo"', source)

    @override_settings(LOCATION_CARTO_BASEMAP_KEY='test-carto-public-key',
                       LOCATION_MAPTILER_BASEMAP_KEY='test-maptiler-public-key')
    def test_public_browser_keys_are_only_rendered_to_staff_map(self):
        url = reverse('location_tracking:map')
        self.client.force_login(self.staff)
        response = self.client.get(url)
        self.assertContains(response, 'data-carto-key="test-carto-public-key"')
        self.assertContains(response, 'data-maptiler-key="test-maptiler-public-key"')
        self.client.force_login(self.alumnus)
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        self.assertNotIn(b'test-carto-public-key', response.content)
        self.assertNotIn(b'test-maptiler-public-key', response.content)

    def test_feed_has_only_verified_alumni_latest_location(self):
        earlier = self.alumni_loc
        earlier.is_active = False
        earlier.save(update_fields=['is_active'])
        latest = LocationData.objects.create(user=self.alumnus, latitude=9.340000, longitude=123.340000)
        self.client.force_login(self.staff)
        response = self.client.get(reverse('location_tracking:get_locations'))
        self.assertEqual(response.status_code, 200)
        data = response.json()['locations']
        self.assertEqual({item['id'] for item in data}, {self.alumnus.pk, self.second.pk})
        record = next(item for item in data if item['id'] == self.alumnus.pk)
        self.assertEqual(record['position_id'], latest.pk)
        self.assertEqual(record['latitude'], 9.34)
        self.assertEqual(record['course'], 'BSCS')
        self.assertEqual(record['batch'], '2024')
        self.assertEqual(record['location'], 'Dumaguete')
        self.assertIn('T', record['timestamp'])

    def test_old_position_is_not_labeled_online_or_exposed(self):
        stale = timezone.now() - timedelta(days=100)
        LocationData.objects.filter(pk=self.second_loc.pk).update(timestamp=stale)
        self.client.force_login(self.staff)
        results = self.client.get(reverse('location_tracking:get_locations')).json()['locations']
        self.assertNotIn(self.second.pk, {a['id'] for a in results})

    def test_only_verified_alumnus_can_update_own_location(self):
        url = reverse('location_tracking:update_location')
        self.assertEqual(self.client.post(url, {'latitude': 1, 'longitude': 1}).status_code, 302)
        for user in (self.staff, self.unverified):
            self.client.force_login(user)
            self.assertEqual(self.client.post(url, {'latitude': 1, 'longitude': 1}).status_code, 403)
        self.client.force_login(self.alumnus)
        self.assertEqual(self.client.get(url).status_code, 405)
        for coords in ({'latitude': 'NaN', 'longitude': '90'}, {'latitude': '100', 'longitude': '0'}, {'latitude': 'x'}, {'latitude': '0', 'longitude': 'Infinity'}):
            self.assertEqual(self.client.post(url, coords).status_code, 400)
        resp = self.client.post(url, data=json.dumps({'latitude': 0, 'longitude': 0}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])
        self.assertFalse(LocationData.objects.get(pk=self.alumni_loc.pk).is_active)
        self.assertEqual(LocationData.objects.filter(user=self.alumnus, is_active=True).count(), 1)

    def test_sharing_status_reports_persisted_pin_not_browser_permission(self):
        url = reverse('location_tracking:sharing_status')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.alumnus)
        payload = self.client.get(url).json()
        self.assertTrue(payload['eligible'])
        self.assertTrue(payload['has_active_location'])
        self.assertIsNotNone(payload['last_shared_at'])
        self.client.post(reverse('location_tracking:stop_sharing'))
        payload = self.client.get(url).json()
        self.assertFalse(payload['has_active_location'])
        self.assertIsNone(payload['last_shared_at'])
        self.client.force_login(self.staff)
        payload = self.client.get(url).json()
        self.assertFalse(payload['eligible'])
        self.assertFalse(payload['has_active_location'])
        self.client.force_login(self.unverified)
        self.assertFalse(self.client.get(url).json()['has_active_location'])

    def test_sharing_status_excludes_stale_active_pin(self):
        LocationData.objects.filter(pk=self.alumni_loc.pk).update(
            timestamp=timezone.now() - timedelta(days=100))
        self.client.force_login(self.alumnus)
        self.assertFalse(self.client.get(reverse('location_tracking:sharing_status')).json()['has_active_location'])

    def test_location_meta_contains_status_endpoint_and_csrf_token(self):
        from pathlib import Path
        from django.conf import settings
        for template_name in ('base.html', 'base_alumni.html'):
            source = (Path(settings.BASE_DIR) / 'templates' / template_name).read_text()
            self.assertIn("location_tracking:sharing_status", source)
            self.assertIn('name="csrf-token"', source)
        alumni_base = (Path(settings.BASE_DIR) / 'templates' / 'base_alumni.html').read_text()
        self.assertIn('alumni/mobile-page-headers.css', alumni_base)

    def test_stop_sharing_deactivates_previous_pin(self):
        url = reverse('location_tracking:stop_sharing')
        self.client.force_login(self.alumnus)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(LocationData.objects.get(pk=self.alumni_loc.pk).is_active)
        self.assertTrue(self.client.post(url).json()['success'])
        self.assertFalse(LocationData.objects.get(pk=self.alumni_loc.pk).is_active)
        self.client.force_login(self.staff)
        self.assertNotIn(self.alumnus.pk, {
            entry['id'] for entry in self.client.get(reverse('location_tracking:get_locations')).json()['locations']
        })

    def test_stop_sharing_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alumnus)
        self.assertEqual(client.post(reverse('location_tracking:stop_sharing')).status_code, 403)
        self.assertTrue(LocationData.objects.get(pk=self.alumni_loc.pk).is_active)

    def test_location_update_has_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alumnus)
        response = client.post(reverse('location_tracking:update_location'), {'latitude': 1, 'longitude': 2})
        self.assertEqual(response.status_code, 403)

    def test_geocoder_is_staff_only_and_rejects_unverified_and_inactive(self):
        url = reverse('location_tracking:lookup_address', args=[self.alumni_loc.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.alumnus)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(reverse('location_tracking:lookup_address', args=[self.staff_loc.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('location_tracking:lookup_address', args=[self.unverified_loc.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('location_tracking:lookup_address', args=[999999])).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 503)

    @override_settings(LOCATION_GEOCODER_CONTACT_EMAIL='maps@example.org')
    @patch('location_tracking.views.urlopen')
    def test_lookup_on_demand_caches_response_and_throttles_requests(self, mock_urlopen):
        response = io.BytesIO(json.dumps({'address': {'house_number': '12', 'road': 'Rizal Avenue', 'city': 'Dumaguete', 'state': 'Negros Oriental'}}).encode())
        mock_urlopen.return_value.__enter__.return_value = response
        self.client.force_login(self.staff)
        url = reverse('location_tracking:lookup_address', args=[self.alumni_loc.pk])
        first = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertIn('12 Rizal Avenue', first.json()['address'])
        self.assertEqual(first.json()['precision'], 'street')
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(mock_urlopen.call_count, 1)
        req = mock_urlopen.call_args.args[0]
        self.assertIn('NORSUAlumniMap', req.get_header('User-agent'))
        second_url = reverse('location_tracking:lookup_address', args=[self.second_loc.pk])
        self.assertEqual(self.client.post(second_url).status_code, 429)

    @override_settings(LOCATION_GEOCODER_CONTACT_EMAIL='maps@example.org')
    @patch('location_tracking.views.urlopen')
    def test_area_level_address_is_not_described_as_precise_street(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value = io.BytesIO(json.dumps({'address': {'city': 'Dumaguete'}}).encode())
        self.client.force_login(self.staff)
        response = self.client.post(reverse('location_tracking:lookup_address', args=[self.alumni_loc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['precision'], 'area')
        self.assertIn('approximate', response.json()['note'])
