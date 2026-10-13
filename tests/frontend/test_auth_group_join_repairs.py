import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


class AuthAndGroupJoinSourceChecks(unittest.TestCase):
    def read(self, p):
        return (ROOT / p).read_text()

    def test_join_is_post_only_for_side_effects_and_security_questions_are_verified(self):
        views = self.read('alumni_groups/views.py')
        join = views.split('def join_group(request, slug):', 1)[1].split('def get_leave_group', 1)[0]
        self.assertIn("if request.method == 'POST':", join)
        self.assertIn('SecurityQuestionAnswer.objects.update_or_create(', join)
        self.assertIn('group.has_security_questions', join)
        self.assertIn('if errors:', join)
        self.assertIn('status = \'PENDING\' if', join)
        self.assertIn('def _unanswered_required_questions', views)
        self.assertIn('Required membership answers are missing.', views)

    def test_member_actions_use_bootstrap_modal_not_browser_confirm(self):
        js = self.read('static/js/modules/alumni-groups.js')
        member = js.split('// Confirm member actions using the same-page Bootstrap modal', 1)[1].split('// Handle viewing security answers', 1)[0]
        self.assertNotIn('confirm(', member)
        self.assertIn('bootstrap.Modal.getOrCreateInstance', member)
        self.assertIn('memberActionError', member)
        self.assertIn('groupMemberActionModal', self.read('templates/alumni_groups/manage_members.html'))

    def test_missing_answers_have_helpful_feedback(self):
        self.assertIn('missing_required', self.read('alumni_groups/views.py'))
        self.assertIn('No membership question answers were submitted.', self.read('static/js/modules/alumni-groups.js'))
        self.assertIn('Complete membership questions', self.read('templates/alumni_groups/group_detail.html'))

    def test_auth_ui_is_actual_login_template_and_shared_scoped_css(self):
        self.assertIn("name='account_login'", self.read('norsu_alumni/urls.py'))
        login = self.read('templates/account/login.html')
        self.assertIn('auth-public--login', login)
        self.assertIn('Create Account', login)
        self.assertIn('authFormHeading', login)
        self.assertIn('auth-public--login .auth-card', self.read('static/css/public_auth.css'))
        self.assertIn("static 'css/public_auth.css'", self.read('templates/components/auth_public_head.html'))

    def test_group_footer_gap_fix_is_scoped(self):
        css = self.read('static/css/alumni/layout.css')
        self.assertIn('.alumni-main[data-feature="alumni_groups"]', css)
        self.assertIn('min-height: 0', css)
        self.assertIn('authenticated-footer', self.read('templates/base_alumni.html'))


if __name__ == '__main__':
    unittest.main()
