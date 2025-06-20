from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Donation, Campaign, CampaignType

class DonationForm(forms.ModelForm):
    """Form for making donations"""
    
    class Meta:
        model = Donation
        fields = [
            'amount', 'payment_method', 'is_anonymous', 
            'message', 'donor_name', 'donor_email'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '0.01',
                'placeholder': _('Enter amount')
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
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
            # If user is not authenticated, make donor_name and donor_email required
            self.fields['donor_name'].required = True
            self.fields['donor_email'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        
        # Validate amount is positive
        if amount and amount <= 0:
            self.add_error('amount', _('Amount must be greater than zero.'))
        
        # If anonymous user, ensure donor_name and donor_email are provided
        if not self.user or not self.user.is_authenticated:
            donor_name = cleaned_data.get('donor_name')
            donor_email = cleaned_data.get('donor_email')
            
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
        
        # Set default status to pending
        instance.status = 'pending'
        
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
            'status', 'is_featured'
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
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only staff or superusers can set is_featured flag
        if self.user and not (self.user.is_staff or self.user.is_superuser):
            self.fields['is_featured'].widget = forms.HiddenInput()
            self.fields['is_featured'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        goal_amount = cleaned_data.get('goal_amount')
        
        # Validate end date is after start date
        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', _('End date must be after start date.'))
        
        # Validate goal amount is positive
        if goal_amount and goal_amount <= 0:
            self.add_error('goal_amount', _('Goal amount must be greater than zero.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set created_by if this is a new campaign
        if not instance.pk and self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance 