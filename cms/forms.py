from django import forms
from django.forms import ModelForm, inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit
from .models import (
    SiteConfig, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial,
    AlumniStatistic, NORSUVMGOHistory
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


class HeroSectionForm(ModelForm):
    """Form for editing hero section content"""
    
    class Meta:
        model = SiteConfig
        fields = [
            'hero_headline',
            'hero_subheadline',
            'hero_background_image',
            'hero_primary_cta_text',
            'hero_secondary_cta_text',
            'hero_microcopy',
            'hero_alumni_count',
            'hero_opportunities_count',
            'hero_countries_count',
            'hero_variant',
        ]
        widgets = {
            'hero_headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter main headline (6-10 words recommended)',
                'maxlength': 200,
            }),
            'hero_subheadline': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter subheadline (15-25 words recommended)',
            }),
            'hero_background_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'hero_primary_cta_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter primary CTA button text (2-4 words)',
                'maxlength': 100,
            }),
            'hero_secondary_cta_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter secondary CTA button text (2-3 words)',
                'maxlength': 100,
            }),
            'hero_microcopy': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter microcopy text to reduce friction',
                'maxlength': 200,
            }),
            'hero_alumni_count': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5,000+',
                'maxlength': 50,
            }),
            'hero_opportunities_count': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500+',
                'maxlength': 50,
            }),
            'hero_countries_count': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 30+',
                'maxlength': 50,
            }),
            'hero_variant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., variation-1',
                'maxlength': 50,
            }),
        }
        help_texts = {
            'hero_headline': 'Main headline for the hero section. Keep it concise and benefit-focused (6-10 words).',
            'hero_subheadline': 'Supporting text that expands on the headline (15-25 words).',
            'hero_background_image': 'Upload a background image for the hero section. Recommended size: 1920x600px, optimized to < 500KB for best performance.',
            'hero_primary_cta_text': 'Primary call-to-action button text (2-4 words).',
            'hero_secondary_cta_text': 'Secondary call-to-action button text (2-3 words).',
            'hero_microcopy': 'Small text below CTAs to reduce friction (e.g., "Takes 2 minutes • No credit card required").',
            'hero_alumni_count': 'Number of verified alumni to display (e.g., "5,000+").',
            'hero_opportunities_count': 'Number of career opportunities to display (e.g., "500+").',
            'hero_countries_count': 'Number of countries represented (e.g., "30+").',
            'hero_variant': 'Current hero section variant for A/B testing (e.g., "variation-1").',
        }


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




class VMGOSectionForm(ModelForm):
    """Form for editing VMGO section content"""
    
    class Meta:
        model = NORSUVMGOHistory
        fields = [
            'section_title',
            'is_active',
            'about_title',
            'about_content',
            'vision_title',
            'vision',
            'mission_title',
            'mission',
            'goals_title',
            'goals',
            'values_title',
            'core_values',
            'quality_policy',
            'quality_objectives_title',
            'quality_objective_1',
            'quality_objective_2',
            'quality_objective_3',
            'quality_objective_4',
            'quality_objectives_footer',
        ]
        
        widgets = {
            'section_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., NORSU Vision, Mission, Goals & Core Values'
            }),
            'about_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., About NORSU'
            }),
            'about_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Brief introduction about NORSU...'
            }),
            'vision_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., NORSU Vision'
            }),
            'vision': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Vision statement...'
            }),
            'mission_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., NORSU Mission'
            }),
            'mission': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mission statement...'
            }),
            'goals_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Strategic Goals'
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Format: ASPIRE\n\nA\nAchieve global recognition by program excellence\n\nS\nStrengthen research through impactful innovation\n\n...'
            }),
            'values_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Core Values'
            }),
            'core_values': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Format: SHINE\n\nS\nSpirituality\n\nH\nHonesty\n\n...'
            }),
            'quality_policy': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'NORSU Quality Policy statement...'
            }),
            'quality_objectives_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Quality Objectives'
            }),
            'quality_objective_1': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'First quality objective (O)...'
            }),
            'quality_objective_2': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Second quality objective (D)...'
            }),
            'quality_objective_3': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Third quality objective (A)...'
            }),
            'quality_objective_4': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Fourth quality objective (A)...'
            }),
            'quality_objectives_footer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Footer text for quality objectives section...'
            }),
        }
        
        help_texts = {
            'section_title': 'Main title for the VMGO section.',
            'is_active': 'Show or hide this section on the homepage.',
            'about_title': 'Title for the About NORSU section.',
            'about_content': 'Brief introduction about NORSU (200-300 words recommended).',
            'vision_title': 'Title for the Vision section.',
            'vision': 'Vision statement (50-100 words recommended).',
            'mission_title': 'Title for the Mission section.',
            'mission': 'Mission statement (100-150 words recommended).',
            'goals_title': 'Title for the Goals section (e.g., "Strategic Goals").',
            'goals': 'Format each letter on a new line followed by its description. Example:\n\nA\nAchieve global recognition by program excellence\n\nS\nStrengthen research through impactful innovation',
            'values_title': 'Title for the Core Values section.',
            'core_values': 'Format each letter on a new line followed by its description. Example:\n\nS\nSpirituality\n\nH\nHonesty',
            'quality_policy': 'NORSU Quality Policy statement (100-200 words recommended).',
            'quality_objectives_title': 'Title for the Quality Objectives section.',
            'quality_objective_1': 'First quality objective (O) - Organize.',
            'quality_objective_2': 'Second quality objective (D) - Develop.',
            'quality_objective_3': 'Third quality objective (A) - Achieve.',
            'quality_objective_4': 'Fourth quality objective (A) - Assure.',
            'quality_objectives_footer': 'Footer text for quality objectives section (e.g., compliance statement).',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Section Configuration',
                'section_title',
                'is_active',
            ),
            Fieldset(
                'About NORSU',
                'about_title',
                'about_content',
            ),
            Fieldset(
                'Vision & Mission',
                Row(
                    Column('vision_title', css_class='col-md-6'),
                    Column('mission_title', css_class='col-md-6'),
                ),
                Row(
                    Column('vision', css_class='col-md-6'),
                    Column('mission', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Goals',
                'goals_title',
                'goals',
            ),
            Fieldset(
                'Core Values',
                'values_title',
                'core_values',
            ),
            Fieldset(
                'Quality Policy',
                'quality_policy',
            ),
            Fieldset(
                'Quality Objectives (ODAA)',
                'quality_objectives_title',
                'quality_objective_1',
                'quality_objective_2',
                'quality_objective_3',
                'quality_objective_4',
                'quality_objectives_footer',
            ),
            Submit('submit', 'Save Changes', css_class='btn btn-primary')
        )
