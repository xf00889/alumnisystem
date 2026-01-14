"""
Forms for User Management Admin feature
"""
from django import forms
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re


class UserCreationForm(forms.ModelForm):
    """
    Form for creating new user accounts in the admin dashboard.
    
    Validates:
    - Email uniqueness
    - Password complexity (min 8 chars, uppercase, lowercase, number, special char)
    - Password confirmation matching
    
    Requirements: 1.2, 1.5, 8.1, 8.2
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'autocomplete': 'off'
        }),
        help_text='User will receive login credentials at this email address'
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        }),
        help_text='User\'s first name'
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        }),
        help_text='User\'s last name'
    )
    
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        help_text='Password must be at least 8 characters with uppercase, lowercase, number, and special character'
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password',
        help_text='Re-enter the password to confirm'
    )
    
    send_welcome_email = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Send welcome email',
        help_text='Send login credentials to the user via email'
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
    
    def clean_email(self):
        """
        Validate email format and uniqueness.
        
        Requirements: 1.5, 8.1
        """
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError('Please enter a valid email address.')
        
        # Check uniqueness
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists. '
                'Please search for the existing user or use a different email address.'
            )
        
        return email
    
    def clean_password(self):
        """
        Validate password complexity.
        
        Requirements: 8.2
        """
        password = self.cleaned_data.get('password', '')
        
        # Minimum length check (already enforced by min_length, but double-check)
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for digit
        if not re.search(r'\d', password):
            raise forms.ValidationError('Password must contain at least one number.')
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password):
            raise forms.ValidationError('Password must contain at least one special character.')
        
        return password
    
    def clean(self):
        """
        Validate password confirmation matching.
        
        Requirements: 8.2
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError({
                    'password_confirm': 'Passwords do not match. Please ensure both passwords are identical.'
                })
        
        return cleaned_data


class UserSearchForm(forms.Form):
    """
    Form for searching and filtering users in the user management interface.
    
    Provides search by name/email and filtering by role and status.
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    
    ROLE_CHOICES = [
        ('', 'All Roles'),
        ('alumni', 'Alumni'),
        ('mentor', 'Mentor'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
        ('superuser', 'Superuser'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or email...',
            'autocomplete': 'off'
        }),
        label='Search',
        help_text='Search users by email, first name, or last name'
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Role',
        help_text='Filter by user role'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status',
        help_text='Filter by account status'
    )
    
    def clean_search(self):
        """Clean and normalize search query"""
        search = self.cleaned_data.get('search', '').strip()
        return search
