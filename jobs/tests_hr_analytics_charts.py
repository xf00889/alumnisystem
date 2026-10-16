"""Chart.js feature parity and active HR tab contract."""
from pathlib import Path
from django.test import SimpleTestCase
ROOT=Path(__file__).resolve().parent.parent

class HRChartUIContract(SimpleTestCase):
    def test_dashboard_has_chart_data_and_preserves_tables(self):
        template=(ROOT/'jobs/templates/jobs/hr/dashboard.html').read_text()
        self.assertIn('hrApplicationChart',template)
        self.assertIn('hrJobSourcesChart',template)
        self.assertIn('Recent portal applications',template)
    def test_active_navigation_is_scoped_to_selected_hr_tab(self):
        template=(ROOT/'jobs/templates/jobs/hr/base.html').read_text()
        self.assertIn('aria-current="page"',template)
        self.assertIn('request.resolver_match.url_name',template)
