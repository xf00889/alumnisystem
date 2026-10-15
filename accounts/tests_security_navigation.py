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

    def test_security_dashboard_breadcrumb_uses_feature_page_spacing(self):
        template = self.source('templates/accounts/security_dashboard.html')
        css = self.source('static/css/alumni/security.css')
        container_start = template.index('<div class="security-dashboard">')
        breadcrumb = template.index("'alumni/components/breadcrumbs.html'")
        self.assertGreater(breadcrumb, container_start)
        self.assertIn('within_page_shell=True', template)
        self.assertIn('.security-dashboard > .container > .alumni-journey', css)
        self.assertIn('padding: 1.05rem 0 .85rem', css)


    def test_compact_security_dashboard_has_scoped_profile_like_layout(self):
        template = self.source('templates/accounts/security_dashboard.html')
        css = self.source('static/css/alumni/security.css')
        self.assertIn('class="dashboard-header security-hero"', template)
        self.assertIn('class="row g-3 align-items-start"', template)
        self.assertIn('class="col-lg-7"', template)
        self.assertIn('class="col-lg-5"', template)
        self.assertIn('class="security-item__main"', template)
        self.assertIn('security-checklist', template)
        self.assertIn('{% if use_alumni_layout %}', template)
        self.assertIn("{% static 'css/alumni/security.css' %}", template)
        self.assertIn("{% static 'css/modules/accounts.css' %}", template)
        self.assertIn('body.alumni-portal .alumni-main[data-feature="accounts"] .security-dashboard', css)
        self.assertIn('display: flex; flex-direction: row; align-items: flex-start;', css)
        self.assertIn('@media (max-width: 575.98px)', css)
        self.assertIn('Enable email verification', template)
        self.assertIn('Manage 2FA and recovery codes', template)

    def test_security_dashboard_uses_shared_feature_page_width(self):
        security_css = self.source('static/css/alumni/security.css')
        foundation_css = self.source('static/css/alumni/page-foundation.css')
        self.assertIn('width:min(calc(100% - 3rem),1280px);max-width:1280px;', foundation_css)
        self.assertIn('width: min(calc(100% - 3rem), 1280px);', security_css)
        self.assertIn('max-width: 1280px;', security_css)
        self.assertIn('width: min(calc(100% - 1.5rem), 1280px);', security_css)
        self.assertNotIn('max-width: 1160px', security_css)

    def test_groups_filter_styles_do_not_override_alumni_account_dropdown(self):
        css = self.source('static/css/modules/alumni-groups.css')
        # Use plain CSS string assertions as a cross-platform regression test;
        # navigation/dropdown CSS must remain the source of truth for account menus.
        self.assertIn('.filter-dropdown > .dropdown-menu', css)
        self.assertIn('.filter-dropdown .dropdown-item', css)
        self.assertNotIn('html.fe-page--alumni-groups-group-list-html .dropdown-menu{', css)
        self.assertNotIn('html.fe-page--alumni-groups-group-list-html .dropdown-item{', css)
