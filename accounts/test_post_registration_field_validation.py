"""Django-backed regression checks for post-registration field-specific errors."""
from django.test import SimpleTestCase
from .forms import PostRegistrationForm


class PostRegistrationFieldValidationTests(SimpleTestCase):
    def form_data(self, **overrides):
        data = {
            'first_name': 'Test',
            'last_name': 'Graduate',
            'campus': 'NORSU-BAIS',
            'college': 'CAS',
            'course_graduated': 'BSCS',
            'graduation_year': '2024',
            'present_occupation': 'Developer',
            'company_name': 'Example Organization',
        }
        data.update(overrides)
        return data

    def test_missing_program_shows_field_error_not_form_wide_error(self):
        form = PostRegistrationForm(self.form_data(course_graduated=''))
        self.assertFalse(form.is_valid())
        self.assertIn('course_graduated', form.errors)
        self.assertNotIn('__all__', form.errors)
        self.assertIn('Please select your course/program.', str(form.errors['course_graduated']))

    def test_missing_campus_shows_field_error(self):
        form = PostRegistrationForm(self.form_data(campus=''))
        self.assertFalse(form.is_valid())
        self.assertIn('campus', form.errors)
        self.assertNotIn('__all__', form.errors)

    def test_mismatched_program_and_college_shows_college_error(self):
        form = PostRegistrationForm(self.form_data(college='CBA'))
        self.assertFalse(form.is_valid())
        self.assertIn('college', form.errors)
        self.assertNotIn('__all__', form.errors)
