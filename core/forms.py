from django import forms
from .recaptcha_fields import DatabaseReCaptchaField
from .recaptcha_widgets import DatabaseReCaptchaV3
from .recaptcha_utils import is_recaptcha_enabled

class ContactForm(forms.Form):
    """
    Contact form with reCAPTCHA protection
    """
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'required': True
        }),
        label='Full Name'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'required': True
        }),
        label='Email Address'
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter message subject',
            'required': True
        }),
        label='Subject'
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your message',
            'rows': 5,
            'required': True
        }),
        label='Message'
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
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters long.')
        return name
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters long.')
        return message
