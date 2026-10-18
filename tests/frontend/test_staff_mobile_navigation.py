"""Source contracts for HR/coordinator mobile navigation; no DB required."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class StaffMobileNavigationTests(unittest.TestCase):
    def test_coordinator_menu_contains_signout_and_accessible_toggle(self):
        html = read('templates/admin/coordinator/navigation.html')
        self.assertIn('aria-controls="coordinator-primary-nav"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertEqual(html.count("{% url 'account_logout' %}"), 1)
        self.assertLess(html.index('class="coordinator-signout-form"'), html.index('</nav>'))
        self.assertIn('class="coordinator-nav-backdrop"', html)
        for name in ('Alumni Management', 'Communications', 'Donations', 'Mentorship', 'Analytics', 'Account'):
            self.assertIn(name, html)

    def test_hr_menu_preserves_actions(self):
        html = read('jobs/templates/jobs/hr/base.html')
        self.assertIn('id="hr-primary-nav"', html)
        self.assertIn('aria-controls="hr-primary-nav"', html)
        self.assertIn('class="hr-nav-backdrop"', html)
        self.assertIn("{% static 'js/admin/hr-navigation.js' %}", html)
        self.assertEqual(html.count("{% url 'account_logout' %}"), 1)
        self.assertLess(html.index('class="hr-nav-signout"'), html.index('</nav>'))
        for name in ('Overview', 'Job Board', 'Manage Jobs', 'Post Job', 'Applications', 'My Profile'):
            self.assertIn(name, html)

    def test_mobile_styles_overlays_not_extra_rows(self):
        css = read('static/css/admin/coordinator-navigation.css')
        self.assertIn('flex-wrap:nowrap', css)
        self.assertIn('.coordinator-topbar.is-menu-open .coordinator-nav', css)
        self.assertIn('position:absolute;top:calc(100% + 5px)', css)
        self.assertIn('coordinator-nav-backdrop', css)
        hr_css = read('static/css/admin/hr-workspace.css')
        self.assertIn('.hr-topbar.hr-menu-open .hr-nav', hr_css)
        self.assertIn('position:absolute;top:calc(100% + 5px)', hr_css)
        self.assertIn('.hr-nav-signout', hr_css)

    def test_navigation_js_supports_keyboard_and_backdrop(self):
        for file in ('static/js/admin/coordinator-navigation.js', 'static/js/admin/hr-navigation.js'):
            script = read(file)
            with self.subTest(file=file):
                self.assertIn('aria-expanded', script)
                self.assertIn('Escape', script)
                self.assertIn("backdrop.addEventListener('click'", script)
                self.assertIn("mobileQuery.addEventListener('change'", script)
                self.assertIn('setOpen(false', script) if file.endswith('/hr-navigation.js') else self.assertIn('setMobileOpen(false', script)


if __name__ == '__main__':
    unittest.main()
