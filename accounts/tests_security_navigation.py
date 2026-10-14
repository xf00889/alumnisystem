"""Source-level regression guard for MFA public vs authenticated navigation."""
from pathlib import Path
from django.conf import settings
from django.test import SimpleTestCase


class SecurityNavigationSourceTests(SimpleTestCase):
    @staticmethod
    def source(relative_path):
        return (Path(settings.BASE_DIR) / relative_path).read_text(encoding="utf-8")

    def test_login_challenge_has_no_protected_dashboard_link(self):
        public_base = self.source("templates/mfa/base.html")
        self.assertNotIn("accounts:security_dashboard", public_base)
        self.assertNotIn("security_breadcrumbs.html", public_base)
        self.assertIn("{% url 'account_login' %}", self.source("templates/mfa/authenticate.html"))

    def test_signed_in_security_breadcrumbs_are_guarded(self):
        component = self.source("templates/accounts/components/security_breadcrumbs.html")
        self.assertIn("{% if user.is_authenticated %}", component)
        self.assertIn('aria-current="page"', component)
        self.assertIn('aria-label="Account security breadcrumb"', component)
        self.assertIn("accounts:security_dashboard", component)

    def test_authenticated_mfa_pages_share_navigation(self):
        base = self.source("templates/mfa/management_base.html")
        self.assertIn("security_breadcrumbs.html", base)
        self.assertNotIn("mfa-back", base)
        for name in (
            "templates/mfa/totp/activate_form.html",
            "templates/mfa/totp/deactivate_form.html",
            "templates/mfa/recovery_codes/index.html",
            "templates/mfa/recovery_codes/generate.html",
            "templates/mfa/reauthenticate.html",
            "templates/account/reauthenticate.html",
        ):
            with self.subTest(template=name):
                body = self.source(name)
                self.assertIn("{% block security_navigation %}", body)
                self.assertIn("security_breadcrumbs.html", body)

    def test_alumni_and_staff_security_pages_have_contextual_crumbs(self):
        for path in (
            "templates/accounts/alumni_change_password.html",
            "templates/accounts/password_recovery_request.html",
            "templates/accounts/password_recovery_requested.html",
            "templates/accounts/change_password.html",
            "templates/accounts/staff_account_security_form.html",
            "templates/accounts/staff_confirm_email.html",
        ):
            with self.subTest(template=path):
                self.assertIn("security_breadcrumbs.html", self.source(path))
        self.assertNotIn("security_breadcrumbs.html", self.source("templates/accounts/password_recovery_shell.html"))
        self.assertNotIn("security_breadcrumbs.html", self.source("templates/accounts/password_reset_email.html"))

    def test_mobile_centering_is_scoped_to_mfa_challenge(self):
        css = self.source("static/css/auth-mfa.css")
        self.assertIn("body.auth-mfa-page > .mfa-shell", css)
        self.assertIn("justify-content:center", css)
        self.assertIn("@media(max-width:540px)", css)
