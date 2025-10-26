from django import forms
from .models import Announcement, Category
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class AnnouncementForm(forms.ModelForm):
    """Form for creating announcements with CAPTCHA protection"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'priority_level', 'target_audience']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter announcement content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'target_audience': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )

class AnnouncementUpdateForm(forms.ModelForm):
    """Form for editing announcements with is_active field"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'priority_level', 'target_audience', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter announcement content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'target_audience': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )

class PublicAnnouncementForm(forms.ModelForm):
    """Form for creating public announcements with CAPTCHA protection"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'priority_level']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter announcement content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority_level': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )