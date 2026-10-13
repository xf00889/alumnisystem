"""Regression checks for the post-registration academic field validation layout.

Can run offline without Django; integration tests are separate.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'templates/accounts/post_registration.html'
CSS = ROOT / 'static/css/auth-profile-completion.css'
FORMS = ROOT / 'accounts/forms.py'


class PostRegistrationValidationLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE.read_text(encoding='utf-8')
        cls.css = CSS.read_text(encoding='utf-8')
        cls.forms = FORMS.read_text(encoding='utf-8')
        cls.post_clean = cls.forms[cls.forms.index('class PostRegistrationForm'):]

    def test_error_summary_not_rendered_as_a_grid_cell(self):
        self.assertNotIn('{{ form|crispy }}', self.template)
        self.assertIn('{% for field in form %}', self.template)
        self.assertIn('{{ field|as_crispy_field }}', self.template)
        self.assertIn('class="profile-form-errors"', self.template)
        self.assertIn('grid-column: 1 / -1', self.css)

    def test_program_validation_bound_to_course_field(self):
        self.assertIn("error_messages={'required': 'Please select your course/program.'}", self.post_clean)
        self.assertIn("self.add_error('course_graduated'", self.post_clean)
        self.assertNotIn('raise forms.ValidationError("Please select your course/program.")', self.post_clean)

    def test_dependent_controls_preserve_postback_selection_and_inline_validation(self):
        self.assertIn('const savedCollege = collegeSelect.value;', self.template)
        self.assertIn('const savedCourse = courseSelect.value;', self.template)
        self.assertIn('function displayInlineError(field, message)', self.template)
        self.assertIn('event.stopImmediatePropagation();', self.template)
        self.assertIn('aria-invalid', self.template)
        self.assertIn('id="duplicateCheckBanner"', self.template)

    def test_existing_form_and_fraud_safeguards_retained(self):
        self.assertIn('id="postRegForm"', self.template)
        self.assertIn('{% csrf_token %}', self.template)
        self.assertIn("{% url 'accounts:cancel_registration' %}", self.template)
        self.assertIn('DUPLICATE_CHECK_URL', self.template)
        self.assertIn('majorsByCampusProgram', self.template)


if __name__ == '__main__':
    unittest.main()
