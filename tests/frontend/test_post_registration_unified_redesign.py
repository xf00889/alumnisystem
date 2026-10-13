"""Source checks for the post-registration screen matching unified account access.

The full Django form and dependent-select workflows need integration testing separately.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'templates/accounts/post_registration.html'
STYLES = ROOT / 'static/css/auth-profile-completion.css'


class PostRegistrationUnifiedRedesignTests(unittest.TestCase):
    def test_real_post_registration_template_loads_focused_css(self):
        content = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn("{% static 'css/auth-profile-completion.css' %}", content)
        self.assertIn('auth-public--post-registration auth-public--journey', content)
        self.assertIn('components/university_header.html', content)
        self.assertIn('class="auth-brand-top"', content)
        self.assertIn('class="auth-brand-benefits"', content)
        self.assertIn('class="profile-completion-guide"', content)

    def test_registration_form_integrations_unchanged(self):
        content = TEMPLATE.read_text(encoding='utf-8')
        for marker in (
            '{{ form|crispy }}', '{% csrf_token %}', 'id="postRegForm"',
            'id="cancelRegForm"', 'id="duplicateCheckBanner"',
            'id="submitBtn"', 'id="id_campus"', 'id="id_college"',
            'id="id_course_graduated"', 'id="id_major"',
        ):
            if marker.startswith('id="id_'):
                self.assertIn(marker[4:-1], content)  # referenced via JS selectors
            else:
                self.assertIn(marker, content)
        self.assertIn('programsByCampus', content)
        self.assertIn('coursesByCollege', content)
        self.assertIn('majorsByProgram', content)
        self.assertIn("{% url 'accounts:cancel_registration' %}", content)

    def test_responsive_layout_scoped_to_only_this_page(self):
        css = STYLES.read_text(encoding='utf-8')
        self.assertIn('body.auth-public--journey.auth-public--post-registration', css)
        for marker in ('@media(max-width:940px)', '@media(max-width:900px)', '@media(max-width:520px)',
                       'prefers-reduced-motion:reduce', 'grid-template-columns:minmax(0,1fr)'):
            self.assertIn(marker, css)


if __name__ == '__main__':
    unittest.main()
