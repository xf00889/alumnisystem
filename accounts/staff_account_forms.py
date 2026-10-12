"""Validated staff self-service credential forms; unrelated alumni fields are excluded."""

from allauth.account.models import EmailAddress
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()


class StaffPasswordChangeForm(PasswordChangeForm):
    """Require the existing usable password and Django's configured validators."""

    old_password = forms.CharField(
        label='Current password', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label='New password', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label='Confirm new password', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )


class StaffEmailChangeForm(forms.Form):
    new_email = forms.EmailField(
        label='New email address', max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'}),
    )
    current_password = forms.CharField(
        label='Current password', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email'].strip().lower()
        if not new_email or new_email == (self.user.email or '').strip().lower():
            raise forms.ValidationError('Enter an email address different from your current one.')
        if email_is_owned_by_another_user(new_email, self.user.pk):
            raise forms.ValidationError('This email address is already in use.')
        return new_email

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.user.has_usable_password():
            raise forms.ValidationError('Your account has no local password. Use password recovery to set one first.')
        if not self.user.check_password(password):
            raise forms.ValidationError('Incorrect current password.')
        return password


def email_is_owned_by_another_user(email, user_pk):
    """Block cross-account collisions in both Django and allauth login identities."""
    return (
        User.objects.filter(email__iexact=email).exclude(pk=user_pk).exists()
        or EmailAddress.objects.filter(email__iexact=email).exclude(user_id=user_pk).exists()
    )
