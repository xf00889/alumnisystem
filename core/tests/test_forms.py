"""
Tests for user management forms in core.forms.user_management_forms module.

These tests verify form validation for UserCreationForm and UserSearchForm.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from core.forms.user_management_forms import UserCreationForm, UserSearchForm

User = get_user_model()


class UserCreationFormTest(TestCase):
    """Test cases for UserCreationForm"""
    
    def setUp(self):
        """Set up test data"""
        # Create an existing user for uniqueness tests
        self.existing_user = User.objects.create_user(
            email='existing@test.com',
            username='existing',
            password='TestPass123!',
            first_name='Existing',
            last_name='User'
        )
    
    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'ValidPass123!',
            'password_confirm': 'ValidPass123!',
            'send_welcome_email': True
        }
        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_duplicate_email(self):
        """Test that duplicate email is rejected"""
        form_data = {
            'email': 'existing@test.com',
            'first_name': 'Another',
            'last_name': 'User',
            'password': 'ValidPass123!',
            'password_confirm': 'ValidPass123!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already exists', str(form.errors['email']))
    
    def test_invalid_email_format(self):
        """Test that invalid email format is rejected"""
        form_data = {
            'email': 'not-an-email',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'ValidPass123!',
            'password_confirm': 'ValidPass123!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_password_too_short(self):
        """Test that password shorter than 8 characters is rejected"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'Short1!',
            'password_confirm': 'Short1!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
    
    def test_password_no_uppercase(self):
        """Test that password without uppercase is rejected"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'lowercase123!',
            'password_confirm': 'lowercase123!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('uppercase', str(form.errors['password']))
    
    def test_password_no_lowercase(self):
        """Test that password without lowercase is rejected"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'UPPERCASE123!',
            'password_confirm': 'UPPERCASE123!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('lowercase', str(form.errors['password']))
    
    def test_password_no_number(self):
        """Test that password without number is rejected"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'NoNumbers!',
            'password_confirm': 'NoNumbers!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('number', str(form.errors['password']))
    
    def test_password_no_special_char(self):
        """Test that password without special character is rejected"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'NoSpecial123',
            'password_confirm': 'NoSpecial123',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('special character', str(form.errors['password']))
    
    def test_password_mismatch(self):
        """Test that mismatched passwords are rejected"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'ValidPass123!',
            'password_confirm': 'DifferentPass123!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)
        self.assertIn('do not match', str(form.errors['password_confirm']))
    
    def test_missing_required_fields(self):
        """Test that missing required fields are rejected"""
        form_data = {
            'email': 'test@test.com',
            # Missing first_name, last_name, password, password_confirm
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('password', form.errors)
        self.assertIn('password_confirm', form.errors)
    
    def test_email_case_insensitive(self):
        """Test that email comparison is case-insensitive"""
        form_data = {
            'email': 'EXISTING@TEST.COM',  # Same as existing user but uppercase
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'ValidPass123!',
            'password_confirm': 'ValidPass123!',
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already exists', str(form.errors['email']))
    
    def test_send_welcome_email_optional(self):
        """Test that send_welcome_email field is optional"""
        form_data = {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'ValidPass123!',
            'password_confirm': 'ValidPass123!',
            # send_welcome_email not provided
        }
        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")


class UserSearchFormTest(TestCase):
    """Test cases for UserSearchForm"""
    
    def test_empty_form_valid(self):
        """Test that empty form is valid (all fields optional)"""
        form = UserSearchForm(data={})
        self.assertTrue(form.is_valid())
    
    def test_search_only(self):
        """Test form with only search field"""
        form_data = {'search': 'john'}
        form = UserSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search'], 'john')
    
    def test_role_filter_only(self):
        """Test form with only role filter"""
        form_data = {'role': 'admin'}
        form = UserSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['role'], 'admin')
    
    def test_status_filter_only(self):
        """Test form with only status filter"""
        form_data = {'status': 'active'}
        form = UserSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['status'], 'active')
    
    def test_all_fields(self):
        """Test form with all fields populated"""
        form_data = {
            'search': 'john doe',
            'role': 'mentor',
            'status': 'inactive'
        }
        form = UserSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search'], 'john doe')
        self.assertEqual(form.cleaned_data['role'], 'mentor')
        self.assertEqual(form.cleaned_data['status'], 'inactive')
    
    def test_search_whitespace_trimmed(self):
        """Test that search query whitespace is trimmed"""
        form_data = {'search': '  john doe  '}
        form = UserSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search'], 'john doe')
    
    def test_invalid_role_choice(self):
        """Test that invalid role choice is rejected"""
        form_data = {'role': 'invalid_role'}
        form = UserSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)
    
    def test_invalid_status_choice(self):
        """Test that invalid status choice is rejected"""
        form_data = {'status': 'invalid_status'}
        form = UserSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
    
    def test_role_choices_available(self):
        """Test that all expected role choices are available"""
        form = UserSearchForm()
        role_choices = [choice[0] for choice in form.fields['role'].choices]
        
        self.assertIn('', role_choices)  # All Roles
        self.assertIn('alumni', role_choices)
        self.assertIn('mentor', role_choices)
        self.assertIn('hr', role_choices)
        self.assertIn('admin', role_choices)
        self.assertIn('superuser', role_choices)
    
    def test_status_choices_available(self):
        """Test that all expected status choices are available"""
        form = UserSearchForm()
        status_choices = [choice[0] for choice in form.fields['status'].choices]
        
        self.assertIn('', status_choices)  # All Status
        self.assertIn('active', status_choices)
        self.assertIn('inactive', status_choices)
