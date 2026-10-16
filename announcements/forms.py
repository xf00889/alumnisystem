from django import forms
from .models import Announcement, Category
from .audience import COLLEGE_LABELS, PROGRAM_LABELS, normalize_target
from alumni_directory.models import Alumni
from django.utils import timezone
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled



class TargetAudienceFormMixin:
    """Target-specific input appears only for Batch, College, Program, Department."""

    def setup_audience(self):
        field = self.fields['target_value']
        field.required = False  # conditionally validated in clean()
        field.widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'off',
            'maxlength': 200,
            'placeholder': 'Enter the intended audience',
        })
        self.college_suggestions = list(COLLEGE_LABELS.items())
        # Keep common named degrees discoverable. The user may also type an
        # existing program code stored in Alumni.course.
        registered = Alumni.objects.exclude(course='').values_list('course', flat=True).distinct()
        self.program_suggestions = list(PROGRAM_LABELS.items())
        catalog_codes = set(PROGRAM_LABELS)
        self.program_suggestions.extend((value, value) for value in registered if value and value not in catalog_codes)

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get('target_audience')
        target = ' '.join((cleaned.get('target_value') or '').strip().split())
        if kind in ('ALL', 'RECENT'):
            cleaned['target_value'] = ''  # prevent stale audience criteria
            return cleaned
        if kind not in ('BATCH', 'COLLEGE', 'PROGRAM', 'DEPARTMENT'):
            return cleaned
        if not target:
            self.add_error('target_value', 'Specify who should receive this announcement.')
            return cleaned
        if kind == 'BATCH':
            if not (target.isascii() and target.isdecimal() and len(target) == 4):
                self.add_error('target_value', 'Enter a valid four-digit graduation year.')
                return cleaned
            if not 1900 <= int(target) <= timezone.now().year + 1:
                self.add_error('target_value', 'Enter a valid graduation year.')
                return cleaned
        elif kind == 'COLLEGE':
            target = normalize_target(kind, target)
            if target not in COLLEGE_LABELS:
                self.add_error('target_value', 'Choose a college name or code from NORSU colleges.')
                return cleaned
        else:
            target = normalize_target(kind, target)
            # New programs may be registered after this patch: accept an exact
            # program value currently found on an alumni record as well.
            if (target not in PROGRAM_LABELS and
                not Alumni.objects.filter(course__iexact=target).exists()):
                self.add_error('target_value', 'Choose a registered program name or code.')
                return cleaned
        cleaned['target_value'] = target
        return cleaned


class AnnouncementForm(TargetAudienceFormMixin, forms.ModelForm):
    """Form for creating announcements with CAPTCHA protection"""
    
    # Hardcoded category choices as fallback
    CATEGORY_CHOICES = [
        ('', 'Select a category'),
        ('campus-news', 'Campus News'),
        ('events', 'Events'),
        ('career-opportunities', 'Career Opportunities'),
        ('alumni-spotlight', 'Alumni Spotlight'),
        ('fundraising', 'Fundraising'),
        ('volunteer-opportunities', 'Volunteer Opportunities'),
        ('academic-updates', 'Academic Updates'),
        ('community-service', 'Community Service'),
    ]
    
    # Override category field with ChoiceField
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True
    )
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority_level', 'target_audience', 'target_value']
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
            'priority_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'target_audience': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_audience()
        
        # Try to load categories from database, fallback to hardcoded choices
        try:
            categories = Category.objects.all().order_by('name')
            if categories.exists():
                # Use database categories if available
                category_choices = [('', 'Select a category')]
                category_choices.extend([(cat.slug, cat.name) for cat in categories])
                self.fields['category'].choices = category_choices
        except Exception as e:
            # If database query fails, use hardcoded choices (already set)
            pass
        
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
    
    def clean_category(self):
        """Clean and validate category field, return Category instance"""
        category_slug = self.cleaned_data.get('category')
        
        if not category_slug:
            raise forms.ValidationError('Please select a category.')
        
        # Get or create category based on slug
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            # Create category if it doesn't exist
            category_name = dict(self.CATEGORY_CHOICES).get(category_slug, category_slug.replace('-', ' ').title())
            category = Category.objects.create(
                name=category_name,
                slug=category_slug,
                description=f'Auto-created category: {category_name}'
            )
        
        return category

class AnnouncementUpdateForm(TargetAudienceFormMixin, forms.ModelForm):
    """Form for editing announcements with is_active field"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'category', 'priority_level', 'target_audience', 'target_value', 'is_active']
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
        self.setup_audience()
        
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
    
    # Hardcoded category choices as fallback
    CATEGORY_CHOICES = [
        ('', 'Select a category'),
        ('campus-news', 'Campus News'),
        ('events', 'Events'),
        ('career-opportunities', 'Career Opportunities'),
        ('alumni-spotlight', 'Alumni Spotlight'),
        ('fundraising', 'Fundraising'),
        ('volunteer-opportunities', 'Volunteer Opportunities'),
        ('academic-updates', 'Academic Updates'),
        ('community-service', 'Community Service'),
    ]
    
    # Override category field with ChoiceField
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True
    )
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority_level']
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
            'priority_level': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Try to load categories from database, fallback to hardcoded choices
        try:
            categories = Category.objects.all().order_by('name')
            if categories.exists():
                # Use database categories if available
                category_choices = [('', 'Select a category')]
                category_choices.extend([(cat.slug, cat.name) for cat in categories])
                self.fields['category'].choices = category_choices
        except Exception as e:
            # If database query fails, use hardcoded choices (already set)
            pass
        
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
    
    def clean_category(self):
        """Clean and validate category field, return Category instance"""
        category_slug = self.cleaned_data.get('category')
        
        if not category_slug:
            raise forms.ValidationError('Please select a category.')
        
        # Get or create category based on slug
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            # Create category if it doesn't exist
            category_name = dict(self.CATEGORY_CHOICES).get(category_slug, category_slug.replace('-', ' ').title())
            category = Category.objects.create(
                name=category_name,
                slug=category_slug,
                description=f'Auto-created category: {category_name}'
            )
        
        return category
