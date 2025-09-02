from django import forms
from django.utils.translation import gettext_lazy as _
from .models import GCashConfig

class GCashConfigForm(forms.ModelForm):
    class Meta:
        model = GCashConfig
        fields = [
            'name', 'gcash_number', 'account_name', 'qr_code_image', 'instructions', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Configuration Name')}),
            'gcash_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('11-digit PH mobile number')}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Account Name')}),
            'qr_code_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Optional payment instructions') }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        is_active = cleaned.get('is_active')
        qr = cleaned.get('qr_code_image') or getattr(self.instance, 'qr_code_image', None)
        # Require QR when setting active
        if is_active and not qr:
            self.add_error('qr_code_image', _('QR code image is required to activate this configuration.'))
        return cleaned

