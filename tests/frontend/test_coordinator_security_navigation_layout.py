"""Static source checks for coordinator navigation and staff security layout."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class StaffSecurityLayoutTest(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding='utf-8')

    def test_main_icons_and_routes_kept(self):
        html=self.read('templates/admin/coordinator/navigation.html')
        self.assertEqual(html.count("{% url 'account_logout' %}"),1)
        self.assertIn('coordinator-nav-main-icon', html)
        self.assertIn('fa-chart-line', html)
        self.assertIn('fa-user-graduate', html)
        self.assertIn('coordinator-signout-form',html)

    def test_centered_desktop_and_mobile_cutoff_match(self):
        css=self.read('static/css/admin/coordinator-navigation.css')
        js=self.read('static/js/admin/coordinator-navigation.js')
        self.assertIn('min-width:1400px',css)
        self.assertIn('grid-template-columns:minmax(250px,1fr)',css)
        self.assertIn('max-width:1399px',css)
        self.assertIn('max-width: 1399px',js)
        self.assertIn('coordinator-nav-backdrop',css)

    def test_staff_security_card_alignment(self):
        html=self.read('templates/accounts/staff_account_security_form.html')
        css=self.read('static/css/admin/account-profile.css')
        self.assertIn('staff-account-page--security',html)
        self.assertIn('staff-account-title-line',html)
        self.assertIn('staff-account-heading.admin-page-header',css)
        self.assertIn('staff-account-card--form',css)
        self.assertIn('{% csrf_token %}',html)

if __name__=='__main__': unittest.main()
