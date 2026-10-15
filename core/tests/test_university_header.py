from pathlib import Path
import re
from unittest import TestCase


BASE_DIR = Path(__file__).resolve().parents[2]


class UniversityHeaderTest(TestCase):
    def test_header_pairs_the_university_and_alumni_logos(self):
        template = (
            BASE_DIR / "templates" / "components" / "university_header.html"
        ).read_text(encoding="utf-8")

        self.assertIn('class="header-left"', template)
        self.assertIn('class="header-center"', template)
        self.assertIn('class="header-logo-link"', template)
        self.assertIn('class="header-logo-divider"', template)
        self.assertIn('class="norsu-logo"', template)
        self.assertIn('class="alumni-logo"', template)
        self.assertNotIn('class="header-right-alumni"', template)
        self.assertIn("Negros Oriental State University", template)
        self.assertIn("Office of Alumni Affairs", template)
        self.assertIn('aria-label="University identity"', template)
        self.assertIn(
            'aria-label="Go to the NORSU Alumni homepage"',
            template,
        )

    def test_header_css_uses_a_two_column_identity_layout(self):
        css = (
            BASE_DIR / "static" / "css" / "university_header.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "grid-template-columns: auto minmax(0, 1fr);",
            css,
        )
        self.assertIn("background: var(--university-gold);", css)
        self.assertIn(".header-logo-divider", css)

    def test_landing_navbar_does_not_repeat_the_alumni_brand(self):
        landing_template = (
            BASE_DIR / "templates" / "base_landingpage.html"
        ).read_text(encoding="utf-8")

        self.assertNotIn('class="navbar-brand"', landing_template)

    def test_landing_navbar_uses_the_header_height_without_a_gap(self):
        header_css = (
            BASE_DIR / "static" / "css" / "university_header.css"
        ).read_text(encoding="utf-8")
        landing_template = (
            BASE_DIR / "templates" / "base_landingpage.html"
        ).read_text(encoding="utf-8")
        bundled_home_css = (
            BASE_DIR / "static" / "css" / "public-home-bundle.css"
        ).read_text(encoding="utf-8")
        other_public_css = (
            BASE_DIR / "static" / "css" / "modules" / "layout-public.css"
        ).read_text(encoding="utf-8")

        # The university header defines the same height for both routes,
        # including the smaller mobile breakpoint.
        self.assertIn("--university-header-height: 76px;", header_css)
        self.assertIn("height: var(--university-header-height);", header_css)
        self.assertIn("@media (max-width: 767px) {", header_css)
        self.assertIn("--university-header-height: 64px;", header_css)

        # Homepage styles were moved from the template to a generated CSS
        # bundle. Assert the actual navbar rule in both delivered stylesheets
        # rather than requiring obsolete inline CSS in the HTML template.
        navbar_rule = re.compile(r"\.landing-navbar\s*\{([^{}]*)\}", re.S)
        offset = "top: var(--university-header-height, 76px);"
        for label, stylesheet in (
            ("homepage CSS bundle", bundled_home_css),
            ("other public pages CSS", other_public_css),
        ):
            with self.subTest(stylesheet=label):
                blocks = navbar_rule.findall(stylesheet)
                self.assertTrue(
                    any(offset in block for block in blocks),
                    f"{label} must position the navbar directly below the university header",
                )

        self.assertIn("--university-header-height: 64px;", bundled_home_css)
        self.assertIn("versioned_static 'css/public-home-bundle.css'", landing_template)
        self.assertIn("static 'css/modules/layout-public.css'", landing_template)
