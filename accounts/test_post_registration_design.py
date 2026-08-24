from pathlib import Path
from unittest import TestCase


BASE_DIR = Path(__file__).resolve().parents[1]


class PostRegistrationDesignTest(TestCase):
    def test_template_uses_the_shared_public_auth_shell(self):
        template = (
            BASE_DIR / "templates" / "accounts" / "post_registration.html"
        ).read_text(encoding="utf-8")

        self.assertIn("components/auth_public_head.html", template)
        self.assertIn("components/university_header.html", template)
        self.assertIn(
            '<body class="auth-public auth-public--post-registration">',
            template,
        )
        self.assertIn('class="auth-container"', template)
        self.assertIn('class="auth-header"', template)
        self.assertIn('class="auth-card"', template)

    def test_template_preserves_registration_form_hooks(self):
        template = (
            BASE_DIR / "templates" / "accounts" / "post_registration.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="postRegForm"', template)
        self.assertIn("{{ form|crispy }}", template)
        self.assertIn('id="duplicateCheckBanner"', template)
        self.assertIn('id="submitBtn"', template)
        self.assertIn('id="cancelRegForm"', template)

    def test_shared_styles_include_responsive_post_registration_layout(self):
        css = (
            BASE_DIR / "static" / "css" / "public_auth.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "body.auth-public--post-registration .post-reg-form",
            css,
        )
        self.assertIn(
            "grid-template-columns: repeat(2, minmax(0, 1fr));",
            css,
        )
        self.assertIn(
            "body.auth-public--post-registration #div_id_company_name",
            css,
        )
        self.assertIn("@media (max-width: 600px)", css)
        self.assertIn("grid-template-columns: 1fr;", css)
