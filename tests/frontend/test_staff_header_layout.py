"""Static regression checks for administration page header composition.

Run from the repository root:
    python -m unittest discover -s tests/frontend -p 'test_staff_header_layout.py'

These checks do not need Django, a database, or sample content.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

DONATION_NAV_PAGES = (
    'donations/templates/donations/verification_dashboard.html',
    'donations/templates/donations/gcash_list.html',
    'donations/templates/donations/fraud_monitoring_dashboard.html',
    'donations/templates/donations/analytics_dashboard.html',
    'templates/donations/manage_gcash.html',
    'templates/donations/manage_donations.html',
    'templates/donations/manage_campaigns.html',
)

ACTION_ROW_PAGES = (
    'donations/templates/donations/analytics_dashboard.html',
    'donations/templates/donations/fraud_monitoring_dashboard.html',
    'donations/templates/donations/manage_campaigns.html',
    'cms/templates/cms/legal_page_list.html',
    'templates/ai_configuration.html',
    'templates/sso_configuration_list.html',
    'templates/recaptcha_analytics.html',
    'templates/surveys/admin/survey_analytics.html',
    'jobs/templates/jobs/manage_jobs.html',
    'log_viewer/templates/log_viewer/unified_dashboard.html',
    'log_viewer/templates/log_viewer/management_dashboard.html',
    'log_viewer/templates/log_viewer/logs.html',
)


class StaffHeaderCompositionTests(unittest.TestCase):
    def test_donation_tabs_not_duplicated_in_page_body(self):
        for page in DONATION_NAV_PAGES:
            with self.subTest(page=page):
                source = (ROOT / page).read_text(encoding='utf-8')
                self.assertNotIn('donations/components/admin_navigation.html', source)
        self.assertFalse((ROOT / 'templates/donations/components/admin_navigation.html').exists())

    def test_action_headers_use_shared_desktop_layout(self):
        for page in ACTION_ROW_PAGES:
            with self.subTest(page=page):
                source = (ROOT / page).read_text(encoding='utf-8')
                self.assertIn('admin-page-header--action-row', source)
                self.assertIn('admin-page-header__title', source)
                self.assertTrue('href=' in source or '<button' in source)

    def test_header_css_scoped_and_responsive(self):
        source = (ROOT / 'static/css/admin/page-headers.css').read_text(encoding='utf-8')
        self.assertIn('.admin-page-header.admin-page-header--action-row', source)
        self.assertIn('display:flex !important', source)
        self.assertIn('.admin-page-header__nested-row', source)
        self.assertIn('@media (max-width:767.98px)', source)

    def test_core_routes_preserved(self):
        cases = {
            'donations/templates/donations/analytics_dashboard.html': 'donations:verification_dashboard',
            'donations/templates/donations/fraud_monitoring_dashboard.html': 'donations:export_fraud_alerts',
            'templates/ai_configuration.html': 'core:ai_configuration_create',
            'templates/sso_configuration_list.html': 'core:sso_configuration_create',
            'templates/surveys/admin/survey_analytics.html': 'surveys:survey_list',
            'jobs/templates/jobs/manage_jobs.html': 'jobs:post_job',
        }
        for path, route in cases.items():
            with self.subTest(path=path):
                self.assertIn(route, (ROOT / path).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
