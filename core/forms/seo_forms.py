"""
SEO Management Forms

Forms for managing PageSEO and OrganizationSchema models.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, HTML

from core.models.seo import PageSEO, OrganizationSchema


class PageSEOForm(forms.ModelForm):
    """
    Form for creating and editing PageSEO entries.
    
    Features:
    - Crispy-forms styling
    - Custom validation for character counts
    - Help text for optimal SEO values
    - Character count indicators
    
    Requirements: 13.1, 13.4, 13.5
    """
    
    class Meta:
        model = PageSEO
        fields = [
            'page_path', 'meta_title', 'meta_description', 'meta_keywords',
            'og_image', 'twitter_image', 'canonical_url',
            'sitemap_priority', 'sitemap_changefreq', 'is_active'
        ]
        widgets = {
            'page_path': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., / or /about-us/',
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter page title (50-60 characters)',
                'maxlength': '60',
                'id': 'id_meta_title',
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter page description (150-160 characters)',
                'rows': 3,
                'maxlength': '160',
                'id': 'id_meta_description',
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'keyword1, keyword2, keyword3',
            }),
            'canonical_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/page',
            }),
            'sitemap_priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.0',
                'max': '1.0',
                'step': '0.1',
            }),
            'sitemap_changefreq': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up crispy forms helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        self.helper.layout = Layout(
            Fieldset(
                'Page Information',
                'page_path',
                HTML('''
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        <strong>Page Path:</strong> The URL path of the page (e.g., "/" for home, "/about-us/" for about page).
                    </div>
                '''),
            ),
            Fieldset(
                'Meta Tags',
                Row(
                    Column('meta_title', css_class='form-group col-md-12 mb-3'),
                ),
                HTML('''
                    <div class="col-lg-9 offset-lg-3 mb-3">
                        <small class="text-muted">
                            <span id="title-count">0</span> / 60 characters
                            <span id="title-status" class="ms-2"></span>
                        </small>
                    </div>
                '''),
                Row(
                    Column('meta_description', css_class='form-group col-md-12 mb-3'),
                ),
                HTML('''
                    <div class="col-lg-9 offset-lg-3 mb-3">
                        <small class="text-muted">
                            <span id="description-count">0</span> / 160 characters
                            <span id="description-status" class="ms-2"></span>
                        </small>
                    </div>
                '''),
                'meta_keywords',
                HTML('''
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>SEO Best Practices:</strong>
                        <ul class="mb-0 mt-2">
                            <li><strong>Title:</strong> 50-60 characters (optimal for search results)</li>
                            <li><strong>Description:</strong> 150-160 characters (optimal for search results)</li>
                            <li><strong>Keywords:</strong> Comma-separated, relevant to page content</li>
                        </ul>
                    </div>
                '''),
            ),
            Fieldset(
                'Social Media Images',
                'og_image',
                HTML('''
                    <div class="col-lg-9 offset-lg-3 mb-3">
                        <small class="text-muted">
                            <i class="fas fa-image"></i> Recommended: 1200x630 pixels for Open Graph
                        </small>
                    </div>
                '''),
                'twitter_image',
                HTML('''
                    <div class="col-lg-9 offset-lg-3 mb-3">
                        <small class="text-muted">
                            <i class="fab fa-twitter"></i> Recommended: 800x418 pixels for Twitter Card
                        </small>
                    </div>
                '''),
            ),
            Fieldset(
                'SEO Settings',
                'canonical_url',
                Row(
                    Column('sitemap_priority', css_class='form-group col-md-6 mb-3'),
                    Column('sitemap_changefreq', css_class='form-group col-md-6 mb-3'),
                ),
                'is_active',
            ),
            HTML('''
                <div class="form-group row">
                    <div class="col-12 text-center">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Save
                        </button>
                        <a href="{% url 'core:seo_page_list' %}" class="btn btn-secondary">
                            <i class="fas fa-times"></i> Cancel
                        </a>
                    </div>
                </div>
            '''),
        )
    
    def clean_meta_title(self):
        """
        Validate meta title length (50-60 characters recommended).
        
        Requirements: 13.5
        """
        meta_title = self.cleaned_data.get('meta_title', '')
        title_len = len(meta_title)
        
        if title_len < 50 or title_len > 60:
            raise forms.ValidationError(
                f'Meta title should be between 50-60 characters for optimal SEO. '
                f'Current length: {title_len} characters.'
            )
        
        return meta_title
    
    def clean_meta_description(self):
        """
        Validate meta description length (150-160 characters recommended).
        
        Requirements: 13.5
        """
        meta_description = self.cleaned_data.get('meta_description', '')
        desc_len = len(meta_description)
        
        if desc_len < 150 or desc_len > 160:
            raise forms.ValidationError(
                f'Meta description should be between 150-160 characters for optimal SEO. '
                f'Current length: {desc_len} characters.'
            )
        
        return meta_description
    
    def clean_sitemap_priority(self):
        """
        Validate sitemap priority (0.0 to 1.0).
        
        Requirements: 13.5
        """
        priority = self.cleaned_data.get('sitemap_priority')
        
        if priority is not None:
            if priority < 0.0 or priority > 1.0:
                raise forms.ValidationError(
                    'Sitemap priority must be between 0.0 and 1.0.'
                )
        
        return priority


class OrganizationSchemaForm(forms.ModelForm):
    """
    Form for editing OrganizationSchema.
    
    Features:
    - Crispy-forms styling
    - Custom validation for email and URLs
    - Help text for Schema.org fields
    
    Requirements: 13.1
    """
    
    class Meta:
        model = OrganizationSchema
        fields = [
            'name', 'logo', 'url', 'telephone', 'email',
            'street_address', 'address_locality', 'address_region',
            'postal_code', 'address_country', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Organization Name',
            }),
            'logo': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/logo.png',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+63 123 456 7890',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@example.com',
            }),
            'street_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123 Main Street',
            }),
            'address_locality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'address_region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345',
            }),
            'address_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PH',
                'maxlength': '2',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up crispy forms helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        self.helper.layout = Layout(
            Fieldset(
                'Organization Details',
                'name',
                'logo',
                'url',
                HTML('''
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        <strong>Schema.org Organization:</strong> This information will be used to generate structured data for search engines.
                    </div>
                '''),
            ),
            Fieldset(
                'Contact Information',
                Row(
                    Column('telephone', css_class='form-group col-md-6 mb-3'),
                    Column('email', css_class='form-group col-md-6 mb-3'),
                ),
            ),
            Fieldset(
                'Address',
                'street_address',
                Row(
                    Column('address_locality', css_class='form-group col-md-6 mb-3'),
                    Column('address_region', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('postal_code', css_class='form-group col-md-6 mb-3'),
                    Column('address_country', css_class='form-group col-md-6 mb-3'),
                ),
                HTML('''
                    <div class="col-lg-9 offset-lg-3 mb-3">
                        <small class="text-muted">
                            <i class="fas fa-globe"></i> Country code should be ISO 3166-1 alpha-2 (e.g., "PH" for Philippines)
                        </small>
                    </div>
                '''),
            ),
            Fieldset(
                'Status',
                'is_active',
            ),
            HTML('''
                <div class="form-group row">
                    <div class="col-12 text-center">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Save
                        </button>
                        <a href="{% url 'core:seo_page_list' %}" class="btn btn-secondary">
                            <i class="fas fa-times"></i> Cancel
                        </a>
                    </div>
                </div>
            '''),
        )
    
    def clean_address_country(self):
        """
        Validate country code (ISO 3166-1 alpha-2).
        """
        country_code = self.cleaned_data.get('address_country', '').upper()
        
        if country_code and len(country_code) != 2:
            raise forms.ValidationError(
                'Country code must be 2 characters (ISO 3166-1 alpha-2, e.g., "PH").'
            )
        
        return country_code
