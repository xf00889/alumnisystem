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
            '<body class="auth-public auth-public--post-registration auth-public--journey">',
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
        self.assertIn("{{ field|as_crispy_field }}", template)
        self.assertIn("{% for field in form %}", template)
        self.assertIn('id="duplicateCheckBanner"', template)
        self.assertIn('id="submitBtn"', template)
        self.assertIn('id="cancelRegForm"', template)

    def test_page_styles_include_responsive_error_layout(self):
        css = (
            BASE_DIR / "static" / "css" / "auth-profile-completion.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "body.auth-public--journey.auth-public--post-registration .post-reg-form",
            css,
        )
        self.assertIn("grid-column: 1 / -1", css)
        self.assertIn(".profile-form-errors", css)
        self.assertIn("@media(max-width:520px)", css)



class SignupFeedbackDesignTest(TestCase):
    def test_existing_account_error_uses_an_actionable_modal(self):
        template = (
            BASE_DIR / "templates" / "account" / "login.html"
        ).read_text(encoding="utf-8")

        self.assertIn("'user with this email already exists' in message_text", template)
        self.assertIn("title: 'Account Already Exists'", template)
        self.assertIn("confirmButtonText: 'Sign In'", template)
        self.assertIn("denyButtonText: 'Reset Password'", template)
        self.assertIn("window.location.href = \"{% url 'account_reset_password' %}\"", template)
        self.assertIn("ToastUtils.showError('{{ message|escapejs }}')", template)
