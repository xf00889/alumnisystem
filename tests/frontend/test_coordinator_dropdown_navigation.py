"""Source contracts for the grouped coordinator top bar; no Django install required."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
NAV = ROOT / 'templates/admin/coordinator/navigation.html'
CSS = ROOT / 'static/css/admin/coordinator-navigation.css'
JS = ROOT / 'static/js/admin/coordinator-navigation.js'
BASE = ROOT / 'templates/base.html'


class CoordinatorDropdownNavigationTests(unittest.TestCase):
    def test_coordinator_sections_follow_sidebar_without_privileged_modules(self):
        nav = NAV.read_text(encoding='utf-8')
        sidebar = (ROOT / 'templates/admin/components/sidebar.html').read_text(encoding='utf-8')
        sections = ('Alumni Management', 'Communications', 'Donations',
                    'Mentorship', 'Analytics', 'Account')
        self.assertEqual(nav.count('<details class="coordinator-menu-group'), len(sections))
        for section in sections:
            with self.subTest(section=section):
                self.assertIn('>'+section+' <i class="fas fa-chevron-down"', nav)
                self.assertIn('>'+section+'</span>', sidebar)
        for denied in ('jobs:manage_jobs', 'core:user_list', 'core:system_settings',
                       'jobs:hr_dashboard', 'jobs:scraper_dashboard'):
            self.assertNotIn(denied, nav)
        self.assertIn("{% url 'core:coordinator_dashboard' %}", nav)
        self.assertIn("{% url 'account_logout' %}", nav)
        self.assertIn('{% csrf_token %}', nav)

    def test_usable_dropdowns_have_mobile_and_keyboard_behavior(self):
        nav = NAV.read_text(encoding='utf-8')
        css = CSS.read_text(encoding='utf-8')
        script = JS.read_text(encoding='utf-8')
        self.assertIn('aria-controls="coordinator-primary-nav"', nav)
        self.assertIn('aria-expanded="false"', nav)
        self.assertIn('<summary class="coordinator-menu-trigger">', nav)
        self.assertIn('.coordinator-menu-group[open]', css)
        self.assertIn('.coordinator-menu-trigger:focus-visible', css)
        self.assertIn('.is-menu-open .coordinator-nav', css)
        self.assertIn("event.key !== 'Escape'", script)
        self.assertIn("document.addEventListener('pointerdown'", script)
        self.assertIn("group.addEventListener('toggle'", script)

    def test_assets_only_load_inside_coordinator_workspace(self):
        base = BASE.read_text(encoding='utf-8')
        self.assertIn("{% static 'css/admin/coordinator-navigation.css' %}", base)
        self.assertIn("{% static 'js/admin/coordinator-navigation.js' %}", base)
        self.assertIn("{% include 'admin/coordinator/navigation.html' %}", base)


if __name__ == '__main__':
    unittest.main()
