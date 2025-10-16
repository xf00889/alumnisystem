"""
Forms for the setup process.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class InitialSetupForm(forms.Form):
    """Form for basic site configuration."""
    
    site_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your site name'
        }),
        help_text="The name of your alumni system"
    )
    
    site_description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Brief description of your alumni system'
        }),
        help_text="Optional description of your alumni system"
    )
    
    admin_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com'
        }),
        help_text="Email address for the site administrator"
    )
    
    timezone = forms.ChoiceField(
        choices=[
            ('UTC', 'UTC'),
            ('America/New_York', 'Eastern Time'),
            ('America/Chicago', 'Central Time'),
            ('America/Denver', 'Mountain Time'),
            ('America/Los_Angeles', 'Pacific Time'),
            ('Europe/London', 'London'),
            ('Europe/Paris', 'Paris'),
            ('Asia/Tokyo', 'Tokyo'),
            ('Asia/Shanghai', 'Shanghai'),
            ('Asia/Manila', 'Manila'),
            ('Australia/Sydney', 'Sydney'),
        ],
        initial='UTC',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select your timezone"
    )

    def clean_site_name(self):
        site_name = self.cleaned_data.get('site_name')
        if not site_name or len(site_name.strip()) < 2:
            raise ValidationError("Site name must be at least 2 characters long")
        return site_name.strip()


class EmailConfigForm(forms.Form):
    """Form for email server configuration."""
    
    email_backend = forms.ChoiceField(
        choices=[
            ('console', 'Console (for testing only)'),
            ('smtp', 'SMTP Server'),
            ('gmail', 'Gmail'),
        ],
        initial='console',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Choose your email backend"
    )
    
    email_host = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'smtp.gmail.com'
        }),
        help_text="SMTP server hostname"
    )
    
    email_port = forms.IntegerField(
        required=False,
        initial=587,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '587'
        }),
        help_text="SMTP server port (usually 587 for TLS)"
    )
    
    email_use_tls = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Use TLS encryption"
    )
    
    email_host_user = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your-email@gmail.com'
        }),
        help_text="Email address for authentication"
    )
    
    email_host_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email password or app password'
        }),
        help_text="Email password or app-specific password"
    )
    
    default_from_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'noreply@example.com'
        }),
        help_text="Default sender email address"
    )
    
    test_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'test@example.com'
        }),
        help_text="Email address to send test message to"
    )

    def clean(self):
        cleaned_data = super().clean()
        email_backend = cleaned_data.get('email_backend')
        
        if email_backend in ['smtp', 'gmail']:
            # Validate required fields for SMTP
            required_fields = ['email_host', 'email_host_user', 'email_host_password']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"This field is required when using {email_backend}")
        
        return cleaned_data

    def clean_email_port(self):
        port = self.cleaned_data.get('email_port')
        if port and (port < 1 or port > 65535):
            raise ValidationError("Port must be between 1 and 65535")
        return port


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
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists")
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required")
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists")
        
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


class SetupProgressForm(forms.Form):
    """Form for tracking setup progress."""
    
    current_step = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    
    completed_steps = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
