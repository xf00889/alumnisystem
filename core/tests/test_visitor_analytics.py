"""Visitor privacy, IP trust boundary, and admin authorization regression tests."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.middleware.visitor_analytics import VisitorAnalyticsMiddleware, client_ip
from core.models.visitor_analytics import DailyVisitor
from setup.models import SetupState


@override_settings(VISITOR_ANALYTICS_ENABLED=True, VISITOR_TRUSTED_PROXY_IPS=('127.0.0.1',), SECURE_SSL_REDIRECT=False)
class VisitorAnalyticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.superuser = User.objects.create_superuser('traffic-admin', 'traffic-admin@example.com', 'test-password')
        cls.staff = User.objects.create_user('traffic-staff', 'traffic-staff@example.com', 'test-password', is_staff=True)

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = VisitorAnalyticsMiddleware(lambda request: HttpResponse('<html>ok</html>', content_type='text/html'))

    def test_stores_one_daily_record_and_deduplicates(self):
        request = self.factory.get('/about-us/', REMOTE_ADDR='198.51.100.10', HTTP_USER_AGENT='Mozilla/5.0')
        with patch('core.middleware.visitor_analytics.cache.add', return_value=True):
            self.middleware(request)
            self.middleware(request)
        self.assertEqual(DailyVisitor.objects.count(), 1)
        self.assertEqual(DailyVisitor.objects.get().sampled_page_loads, 2)

    def test_forwarded_header_not_trusted_from_arbitrary_client(self):
        request = self.factory.get('/', REMOTE_ADDR='198.51.100.10', HTTP_X_REAL_IP='198.51.100.99')
        self.assertEqual(client_ip(request), '198.51.100.10')

    def test_forwarded_header_only_from_trusted_peer(self):
        request = self.factory.get('/', REMOTE_ADDR='127.0.0.1', HTTP_X_REAL_IP='198.51.100.99')
        self.assertEqual(client_ip(request), '198.51.100.99')

    def test_dnt_and_api_requests_are_not_recorded(self):
        self.middleware(self.factory.get('/', REMOTE_ADDR='198.51.100.11', HTTP_DNT='1'))
        self.middleware(self.factory.get('/api/notifications/', REMOTE_ADDR='198.51.100.11'))
        self.assertEqual(DailyVisitor.objects.count(), 0)

    def test_superuser_only_access(self):
        url = reverse('core:visitor_analytics')
        self.client.force_login(self.staff)
        response = self.client.get(url, secure=True)
        self.assertNotEqual(response.status_code, 200)
        self.client.force_login(self.superuser)
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)

    def test_retention_purge(self):
        from django.core.management import call_command
        from django.conf import settings
        now = timezone.now()
        old = now - timedelta(days=40)
        DailyVisitor.objects.create(day=timezone.localdate(old),ip_address='198.51.100.11',first_seen=old,last_seen=old)
        call_command('purge_visitor_analytics')
        self.assertFalse(DailyVisitor.objects.exists())
