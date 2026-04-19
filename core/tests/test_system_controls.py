from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from core.models import SystemSettings
from core.system_settings_utils import clear_system_settings_cache
from core.view_handlers.error_handlers import handler500


User = get_user_model()


class BaseSystemControlsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.setup_patcher = patch(
            "setup.middleware.SetupRequiredMiddleware._is_setup_complete",
            return_value=True,
        )
        self.setup_patcher.start()
        self.addCleanup(self.setup_patcher.stop)
        clear_system_settings_cache()
        self.addCleanup(clear_system_settings_cache)


class SystemSettingsViewTestCase(BaseSystemControlsTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password="SecurePass123!",
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="SecurePass123!",
            is_staff=True,
        )

    def test_superuser_can_view_and_update_system_settings(self):
        self.client.force_login(self.superuser)
        url = reverse("core:system_settings")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Controls")

        post_response = self.client.post(
            url,
            {
                "maintenance_mode": "on",
                "runtime_debug": "on",
                "maintenance_message": "Scheduled maintenance window",
            },
        )
        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response.url, url)

        settings_obj = SystemSettings.objects.first()
        self.assertIsNotNone(settings_obj)
        self.assertTrue(settings_obj.maintenance_mode)
        self.assertTrue(settings_obj.runtime_debug)
        self.assertEqual(settings_obj.maintenance_message, "Scheduled maintenance window")
        self.assertEqual(settings_obj.updated_by, self.superuser)

    def test_staff_user_cannot_access_system_settings(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("core:system_settings"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("core:admin_dashboard"), response.url)


class MaintenanceModeMiddlewareTestCase(BaseSystemControlsTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            username="maintadmin",
            email="maintadmin@example.com",
            password="SecurePass123!",
        )

    def _enable_maintenance(self, message="Site maintenance ongoing"):
        SystemSettings.objects.create(
            maintenance_mode=True,
            maintenance_message=message,
            runtime_debug=False,
            updated_by=self.superuser,
        )
        clear_system_settings_cache()

    def test_maintenance_off_keeps_public_route_accessible(self):
        response = self.client.get(reverse("core:home"))
        self.assertNotEqual(response.status_code, 503)

    def test_maintenance_on_blocks_public_route_with_503(self):
        self._enable_maintenance("Planned maintenance in progress")
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Planned maintenance in progress", status_code=503)

    def test_maintenance_on_allows_admin_dashboard(self):
        self._enable_maintenance()
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("core:admin_dashboard"))
        self.assertNotEqual(response.status_code, 503)
        self.assertEqual(response.status_code, 200)

    def test_maintenance_on_allows_account_login_route(self):
        self._enable_maintenance()
        response = self.client.get(reverse("account_login"))

        self.assertNotEqual(response.status_code, 503)
        self.assertIn(response.status_code, [200, 302])


class RuntimeDebugHandlersTestCase(BaseSystemControlsTestCase):
    def _set_runtime_debug(self, enabled):
        settings_obj = SystemSettings.objects.order_by("id").first()
        if settings_obj is None:
            settings_obj = SystemSettings.objects.create(
                maintenance_mode=False,
                maintenance_message="The site is under maintenance. Please try again later.",
                runtime_debug=enabled,
            )
        else:
            settings_obj.runtime_debug = enabled
            settings_obj.save()
        clear_system_settings_cache()

    def test_handler500_shows_detailed_output_when_runtime_debug_enabled(self):
        self._set_runtime_debug(True)
        request = self.factory.get("/error-page/")

        response = handler500(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Server Error (500)", response.content)
        self.assertIn(b"Path: /error-page/", response.content)

    def test_handler500_hides_detailed_output_when_runtime_debug_disabled(self):
        self._set_runtime_debug(False)
        request = self.factory.get("/error-page/")

        response = handler500(request)

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b"Path: /error-page/", response.content)
        self.assertNotIn(b"Check logs for details", response.content)

    def test_health_check_returns_runtime_debug_flag(self):
        self._set_runtime_debug(True)
        response_true = self.client.get(reverse("core:health_check"))
        self.assertEqual(response_true.status_code, 200)
        self.assertTrue(response_true.json().get("debug"))

        self._set_runtime_debug(False)
        response_false = self.client.get(reverse("core:health_check"))
        self.assertEqual(response_false.status_code, 200)
        self.assertFalse(response_false.json().get("debug"))
