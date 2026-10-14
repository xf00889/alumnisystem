"""Validation for the admin SMTP form. Never render an existing app password into HTML."""
from django import forms
from core.models.smtp_config import SMTPConfig


class SMTPConfigurationForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        strip=False,
        help_text='For Gmail use a Google App Password; leave blank while editing to retain it.',
    )

    class Meta:
        model = SMTPConfig
        fields = ('name', 'host', 'port', 'use_tls', 'use_ssl', 'username',
                  'password', 'from_email', 'from_name', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Do not let ModelForm treat a blank password edit as a changed secret.
        # The credential is retained by clean_password, not echoed to the browser.
        self.initial['password'] = ''

    def clean_password(self):
        entered = self.cleaned_data.get('password') or ''
        if entered:
            return entered
        if self.instance and self.instance.pk:
            return self.instance.password
        raise forms.ValidationError('An SMTP app password is required.')

    def clean(self):
        data = super().clean()
        data['from_name'] = (data.get('from_name') or '').strip() or 'NORSU Alumni'
        if data.get('is_active') and not (self.instance.pk and self.instance.is_verified):
            # Create/edit saves require a passing SMTP test before activating.
            data['is_active'] = False
        return data
