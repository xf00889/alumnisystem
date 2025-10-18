from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    SiteConfig, PageSection, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial,
    AboutPageConfig, AlumniStatistic
)


class SiteConfigForm(ModelForm):
    """Form for editing site configuration"""
    
    class Meta:
        model = SiteConfig
        fields = [
            'site_name', 'site_tagline', 'logo', 'contact_email', 
            'contact_phone', 'contact_address', 'facebook_url', 
            'twitter_url', 'linkedin_url', 'instagram_url', 
            'youtube_url', 'signup_button_text', 'login_button_text'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter site name'
            }),
            'site_tagline': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter site tagline'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact email'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact phone'
            }),
            'contact_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter contact address'
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Facebook URL'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Twitter URL'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter LinkedIn URL'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Instagram URL'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter YouTube URL'
            }),
            'signup_button_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter signup button text'
            }),
            'login_button_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter login button text'
            }),
        }


class PageSectionForm(ModelForm):
    """Form for editing page sections"""
    
    class Meta:
        model = PageSection
        fields = ['section_type', 'title', 'subtitle', 'content', 'image', 'order', 'is_active']
        widgets = {
            'section_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'section-type-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter section title'
            }),
            'subtitle': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter section subtitle'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter section content'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for section types
        self.fields['section_type'].help_text = self.get_section_type_help_text()
    
    def get_section_type_help_text(self):
        return """
        <div class="section-type-help-icon">
            <i class="fas fa-question-circle" onclick="openSectionTypesModal()" title="Click for section types guide"></i>
        </div>
        """




class StaffMemberForm(ModelForm):
    """Form for editing staff members"""
    
    class Meta:
        model = StaffMember
        fields = ['name', 'position', 'department', 'bio', 'image', 'email', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter staff member name'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter position'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter bio'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TimelineItemForm(ModelForm):
    """Form for editing timeline items"""
    
    class Meta:
        model = TimelineItem
        fields = ['year', 'title', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter year (e.g., 2024)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter timeline title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter timeline description'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter FontAwesome icon class (e.g., fas fa-university)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ContactInfoForm(ModelForm):
    """Form for editing contact information"""
    
    class Meta:
        model = ContactInfo
        fields = ['contact_type', 'value', 'is_primary', 'order', 'is_active']
        widgets = {
            'contact_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter contact information'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class FAQForm(ModelForm):
    """Form for editing FAQs"""
    
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'order', 'is_active']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter FAQ question'
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter FAQ answer'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class FeatureForm(ModelForm):
    """Form for editing features"""
    
    class Meta:
        model = Feature
        fields = ['title', 'content', 'icon', 'icon_class', 'link_url', 'link_text', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter feature title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter feature content'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter FontAwesome icon class (e.g., fas fa-rocket)'
            }),
            'icon_class': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter icon CSS class'
            }),
            'link_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter link URL'
            }),
            'link_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter link text'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TestimonialForm(ModelForm):
    """Form for editing testimonials"""
    
    class Meta:
        model = Testimonial
        fields = ['name', 'position', 'company', 'quote', 'image', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter testimonial author name'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter position'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'quote': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter testimonial quote'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class AboutPageConfigForm(ModelForm):
    """Form for editing About page configuration"""
    
    class Meta:
        model = AboutPageConfig
        fields = [
            'university_name', 'university_short_name', 'university_description',
            'university_extended_description', 'establishment_year', 'mission',
            'vision', 'about_page_title', 'about_page_subtitle'
        ]
        widgets = {
            'university_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full university name'
            }),
            'university_short_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter university acronym'
            }),
            'university_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter main university description'
            }),
            'university_extended_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter extended university description'
            }),
            'establishment_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter establishment year (e.g., 2004)'
            }),
            'mission': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter university mission statement'
            }),
            'vision': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter university vision statement'
            }),
            'about_page_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter About page title'
            }),
            'about_page_subtitle': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter About page subtitle'
            }),
        }


class AlumniStatisticForm(ModelForm):
    """Form for editing alumni statistics"""
    
    class Meta:
        model = AlumniStatistic
        fields = ['statistic_type', 'value', 'label', 'icon', 'icon_color', 'order', 'is_active']
        widgets = {
            'statistic_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter statistic value (e.g., 5,000+)'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter display label'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter FontAwesome icon class (e.g., fas fa-users)'
            }),
            'icon_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': 'Select icon color'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


