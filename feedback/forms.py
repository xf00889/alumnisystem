from django import forms
from django.core.validators import FileExtensionValidator
from .models import Feedback
import os
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class FeedbackForm(forms.ModelForm):
    """Form for users to submit feedback"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].help_text = 'Select the most appropriate category for your feedback'
        self.fields['priority'].help_text = 'Select the urgency level of your feedback'
        self.fields['subject'].help_text = 'Brief summary of your feedback (max 200 characters)'
        self.fields['message'].help_text = 'Provide detailed information about your feedback'
        self.fields['attachment'].help_text = 'Accepted formats: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG (max 5MB)'
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = ReCaptchaField(
                widget=ReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # 5MB limit
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 5MB')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg']
            ext = os.path.splitext(attachment.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'Only the following file types are allowed: {", ".join(allowed_extensions)}')
        return attachment
    
    class Meta:
        model = Feedback
        fields = ['category', 'subject', 'message', 'priority', 'attachment']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Select the most appropriate category for your feedback'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of your feedback',
                'maxlength': '200',
                'data-bs-toggle': 'tooltip',
                'title': 'Enter a brief summary of your feedback',
                'data-char-count': 'true'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please provide detailed information about your feedback...',
                'data-bs-toggle': 'tooltip',
                'title': 'Provide detailed information about your feedback',
                'data-char-count': 'true'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Select the urgency level of your feedback'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg',
                'data-bs-toggle': 'tooltip',
                'title': 'Upload a file to support your feedback (optional)'
            })
        }

class FeedbackAdminForm(forms.ModelForm):
    """Form for admins to manage feedback"""
    class Meta:
        model = Feedback
        fields = ['status', 'priority', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Update the status of this feedback'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Update the priority level'
            }),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add internal notes about this feedback...',
                'data-bs-toggle': 'tooltip',
                'title': 'Add internal notes visible only to administrators'
            })
        } 