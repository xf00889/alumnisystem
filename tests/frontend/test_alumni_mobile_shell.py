"""Source-level regression checks for the shared authenticated alumni mobile shell."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class AuthenticatedMobileShellTests(unittest.TestCase):
    def test_tracer_cta_preserves_destination_and_one_row_layout(self):
        template = read("templates/base_alumni.html")
        css = read("static/css/alumni/layout.css")
        self.assertIn("{% if show_tracer_study_banner %}", template)
        self.assertIn("{% url 'surveys:tracer_study_alumni' %}", template)
        self.assertIn("alumni-tracer-message--compact", template)
        self.assertIn("Tracer study required", template)
        self.assertIn("Answer survey", template)
        self.assertIn(".alumni-tracer-inner { flex-wrap: nowrap", css)
        self.assertIn(".alumni-tracer-message--full { display: none; }", css)
        self.assertIn(".alumni-tracer-message--compact { display: inline; }", css)
        self.assertNotIn(".alumni-tracer-inner { flex-wrap: wrap", css)

    def test_legal_pages_stay_in_public_footer_only(self):
        authenticated = read("templates/components/footer_authenticated.html")
        public = read("templates/components/footer.html")
        self.assertNotIn("legal_pages", authenticated)
        self.assertNotIn("authenticated-footer-legal", authenticated)
        self.assertIn("NORSU Alumni Network", authenticated)
        self.assertIn("legal_pages", public)
        self.assertIn("page.get_absolute_url", public)

    def test_authenticated_mobile_footer_has_space_for_bottom_nav(self):
        css = read("static/css/alumni/authenticated-footer.css")
        self.assertIn("white-space: nowrap", css)
        self.assertIn("max-width: 767px", css)
        self.assertIn(".authenticated-footer-institution { display: none; }", css)
        self.assertIn(".alumni-bottom-nav", css)
        self.assertIn("env(safe-area-inset-bottom)", css)


if __name__ == "__main__":
    unittest.main()
