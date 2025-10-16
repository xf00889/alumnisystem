"""
Forms for the setup process.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class SuperuserForm(forms.Form):
    """Form for creating the initial superuser."""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin'
        }),
        help_text="Username for the superuser account"
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com'
        }),
        help_text="Email address for the superuser account"
    )
    
    password1 = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        help_text="Password must be at least 8 characters long"
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        help_text="Confirm your password"
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("Username is required")
        
        # Validate username format
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters")
        
        # Check if username already exists (with fallback for database issues)
        try:
            if User.objects.filter(username=username).exists():
                raise ValidationError("A user with this username already exists")
        except Exception as e:
            # If database is not ready, skip the check for now
            # The superuser creation will handle this during the actual creation
            pass
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required")
        
        # Check if email already exists (with fallback for database issues)
        try:
            if User.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists")
        except Exception as e:
            # If database is not ready, skip the check for now
            # The superuser creation will handle this during the actual creation
            pass
        
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        
        if password1:
            # Basic password strength validation
            if len(password1) < 8:
                self.add_error('password1', "Password must be at least 8 characters long")
            
            if not re.search(r'[A-Z]', password1):
                self.add_error('password1', "Password must contain at least one uppercase letter")
            
            if not re.search(r'[a-z]', password1):
                self.add_error('password1', "Password must contain at least one lowercase letter")
            
            if not re.search(r'\d', password1):
                self.add_error('password1', "Password must contain at least one number")
        
        return cleaned_data


