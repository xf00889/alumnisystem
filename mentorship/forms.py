from django import forms
from accounts.models import Mentor
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class MentorshipRequestForm(forms.Form):
    """Form for requesting mentorship with CAPTCHA protection"""
    
    skills_seeking = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'What skills are you looking to develop?'
        }),
        help_text='Describe the skills you want to develop through mentorship'
    )
    
    goals = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'What are your career goals?'
        }),
        help_text='Describe your career goals and how mentorship can help'
    )
    
    message = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Why do you want to be mentored by this person?'
        }),
        help_text='Explain why you want to be mentored by this specific mentor'
    )
    
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
    
    def clean(self):
        cleaned_data = super().clean()
        skills_seeking = cleaned_data.get('skills_seeking')
        goals = cleaned_data.get('goals')
        message = cleaned_data.get('message')
        
        if not skills_seeking or not goals or not message:
            raise forms.ValidationError("All fields are required.")
        
        return cleaned_data
