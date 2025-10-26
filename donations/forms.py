from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Donation, Campaign, CampaignType, GCashConfig
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class DonationForm(forms.ModelForm):
    """Form for making donations"""

    class Meta:
        model = Donation
        fields = [
            'amount', 'is_anonymous', 'message', 'donor_name', 'donor_email'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '0.01',
                'placeholder': _('Enter amount')
            }),
            # payment_method removed; GCash is the only option
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Leave a message (optional)')
            }),
            'donor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your name (for non-registered users)')
            }),
            'donor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your email (for non-registered users)')
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.campaign = kwargs.pop('campaign', None)
        super().__init__(*args, **kwargs)

        # If user is authenticated, hide donor_name and donor_email fields
        if self.user and self.user.is_authenticated:
            self.fields['donor_name'].widget = forms.HiddenInput()
            self.fields['donor_email'].widget = forms.HiddenInput()
            self.fields['donor_name'].required = False
            self.fields['donor_email'].required = False
        else:
            # If user is not authenticated, make donor_name and donor_email not required by default
            # We'll handle validation in the clean method based on anonymous status
            self.fields['donor_name'].required = False
            self.fields['donor_email'].required = False
        
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
        amount = cleaned_data.get('amount')

        # Validate amount is positive
        if amount and amount <= 0:
            self.add_error('amount', _('Amount must be greater than zero.'))

        # If anonymous user, ensure donor_name and donor_email are provided (unless anonymous)
        if not self.user or not self.user.is_authenticated:
            is_anonymous = cleaned_data.get('is_anonymous', False)
            donor_name = cleaned_data.get('donor_name')
            donor_email = cleaned_data.get('donor_email')

            # Only require name and email if not anonymous
            if not is_anonymous:
                if not donor_name:
                    self.add_error('donor_name', _('Please provide your name.'))

                if not donor_email:
                    self.add_error('donor_email', _('Please provide your email.'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the campaign
        if self.campaign:
            instance.campaign = self.campaign

        # Set the donor if user is authenticated
        if self.user and self.user.is_authenticated:
            instance.donor = self.user

        # Set default status to pending_payment for GCash donations
        instance.status = 'pending_payment'

        # Set default payment method to GCash
        if not instance.payment_method:
            instance.payment_method = 'gcash'

        if commit:
            instance.save()

        return instance

class CampaignFilterForm(forms.Form):
    """Form for filtering campaigns"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search campaigns...')
        })
    )

    campaign_type = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        required=False,
        choices=[('', _('All Statuses'))] + list(Campaign.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    visibility = forms.ChoiceField(
        required=False,
        choices=[('', _('All Visibility'))] + list(Campaign.VISIBILITY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('recent', _('Most Recent')),
            ('ending_soon', _('Ending Soon')),
            ('progress', _('Most Funded')),
            ('goal', _('Largest Goal')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically populate campaign_type choices
        campaign_types = [('', _('All Types'))]
        for campaign_type in CampaignType.objects.all():
            campaign_types.append((campaign_type.slug, campaign_type.name))

        self.fields['campaign_type'].widget.choices = campaign_types

class CampaignForm(forms.ModelForm):
    """Form for creating and editing campaigns"""

    class Meta:
        model = Campaign
        fields = [
            'name', 'campaign_type', 'short_description', 'description',
            'featured_image', 'goal_amount', 'start_date', 'end_date',
            'status', 'visibility', 'is_featured', 'allow_donations', 'gcash_config'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Campaign Name')
            }),
            'campaign_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Brief description (max 255 characters)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rich-text-editor',
                'rows': 5,
                'placeholder': _('Detailed campaign description')
            }),
            'featured_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'goal_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '0.01',
                'placeholder': _('Target amount')
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_donations': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_allow_donations'
            }),
            'gcash_config': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_gcash_config'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Only staff or superusers can set is_featured flag
        if self.user and not (self.user.is_staff or self.user.is_superuser):
            self.fields['is_featured'].widget = forms.HiddenInput()
            self.fields['is_featured'].required = False

        # Populate GCash config choices
        self.fields['gcash_config'].queryset = GCashConfig.objects.filter(is_active=True)
        self.fields['gcash_config'].empty_label = _("Select GCash Account")
        self.fields['gcash_config'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        goal_amount = cleaned_data.get('goal_amount')
        allow_donations = cleaned_data.get('allow_donations')
        gcash_config = cleaned_data.get('gcash_config')

        # Validate end date is after start date
        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', _('End date must be after start date.'))

        # Validate goal amount is positive
        if goal_amount and goal_amount <= 0:
            self.add_error('goal_amount', _('Goal amount must be greater than zero.'))

        # Validate GCash config is required when donations are allowed
        if allow_donations and not gcash_config:
            self.add_error('gcash_config', _('GCash configuration is required when donations are enabled.'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set created_by if this is a new campaign
        if not instance.pk and self.user:
            instance.created_by = self.user

        if commit:
            instance.save()

        return instance


class PaymentProofForm(forms.ModelForm):
    """Form for uploading payment proof"""
    
    # Add donor_email as a hidden field for unauthenticated users
    donor_email = forms.EmailField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Donation
        fields = ['payment_proof', 'reference_number', 'donor_email']
        widgets = {
            'payment_proof': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'help_text': _('Upload a screenshot of your GCash payment confirmation')
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter GCash transaction reference number (required)')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the donor_email value from the instance
        if self.instance and self.instance.donor_email:
            self.fields['donor_email'].initial = self.instance.donor_email
        self.fields['payment_proof'].required = True
        self.fields['reference_number'].required = True

        # Add help text
        self.fields['payment_proof'].help_text = _(
            'Please upload a clear screenshot of your GCash payment confirmation. '
            'Make sure the amount, date, and reference number are visible.'
        )
        self.fields['reference_number'].help_text = _(
            'Required: Enter the reference number from your GCash transaction receipt.'
        )

    def clean_payment_proof(self):
        proof = self.cleaned_data.get('payment_proof')
        if proof:
            # Check file size (max 5MB)
            if proof.size > 5 * 1024 * 1024:
                raise forms.ValidationError(_('File size must be less than 5MB.'))

            # Check file type
            if not proof.content_type.startswith('image/'):
                raise forms.ValidationError(_('Please upload an image file.'))

        return proof

    def clean(self):
        cleaned_data = super().clean()
        reference_number = cleaned_data.get('reference_number')
        
        # Require reference number for authenticated users
        if not reference_number:
            self.add_error('reference_number', _('Reference number is required. Please enter your GCash transaction reference number.'))
        
        return cleaned_data


class DonationVerificationForm(forms.ModelForm):
    """Form for admin verification of donations"""

    class Meta:
        model = Donation
        fields = ['status', 'verification_notes', 'gcash_transaction_id']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'verification_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Add verification notes...')
            }),
            'gcash_transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('GCash Transaction ID')
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit status choices to verification-relevant options
        self.fields['status'].choices = [
            ('pending_verification', _('Pending Verification')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
            ('disputed', _('Disputed')),
        ]

class GCashConfigForm(forms.ModelForm):
    """Custom form for managing GCash configuration via web UI"""

    class Meta:
        model = GCashConfig
        fields = ['name', 'gcash_number', 'account_name', 'qr_code_image', 'is_active', 'instructions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Configuration Name')}),
            'gcash_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('09123456789')}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Account Name')}),
            'qr_code_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Additional payment instructions')})
        }

    def clean(self):
        cleaned = super().clean()
        is_active = cleaned.get('is_active')
        qr = cleaned.get('qr_code_image')

        # Determine if QR is present (either newly uploaded or existing on the instance)
        has_qr = bool(qr) or (self.instance and self.instance.pk and bool(self.instance.qr_code_image))

        # Require QR code for activation
        if is_active and not has_qr:
            self.add_error('qr_code_image', _('QR code image is required to activate this configuration.'))

        # Only one active configuration at a time
        if is_active:
            qs = GCashConfig.objects.filter(is_active=True)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('is_active', _('Only one GCash configuration can be active at a time. Please deactivate other configurations first.'))

        return cleaned
