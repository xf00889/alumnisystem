"""Anonymous-homepage CSS bundle regressions (no database access)."""
from pathlib import Path
import importlib.util
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class PublicHomeAssetBundleTests(SimpleTestCase):
    def test_bundle_exactly_matches_ordered_sources(self):
        file_path = ROOT / "scripts" / "build_public_home_css.py"
        spec = importlib.util.spec_from_file_location("norsu_public_home_css_builder", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            (ROOT / "static/css/public-home-bundle.css").read_text(encoding="utf-8"),
            module.build(),
            "Regenerate with python scripts/build_public_home_css.py and commit the result",
        )

    def test_home_only_bundle_preserves_other_public_routes(self):
        base = (ROOT / "templates/base_landingpage.html").read_text(encoding="utf-8")
        home = (ROOT / "templates/home.html").read_text(encoding="utf-8")
        self.assertIn("request.resolver_match.url_name == 'home'", base)
        self.assertIn("versioned_static 'css/public-home-bundle.css'", base)
        self.assertIn("request.resolver_match.url_name != 'home'", base)
        self.assertIn("static 'css/landing-performance.css'", base)
        self.assertNotIn("versioned_static 'css/home_redesign.css'", home)
        self.assertNotIn("versioned_static 'css/home_experience.css'", home)
        # Keep the original interactive navbar, toast, and gallery scripts.
        self.assertIn('setMobileMenuState(', base)
        self.assertIn("js/utils/toast-notifications.js", base)
        self.assertIn("js/home_gallery.js", home)

    def test_homepage_ships_single_local_css_request(self):
        base = (ROOT / "templates/base_landingpage.html").read_text(encoding="utf-8")
        self.assertEqual(base.count("'css/public-home-bundle.css'"), 1)
        self.assertIn("'css/public_redesign.css'", base)
        self.assertIn("'css/university_header.css'", base)
