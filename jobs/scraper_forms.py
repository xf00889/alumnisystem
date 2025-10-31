from django import forms
from django.core.validators import MinLengthValidator

class JobScraperForm(forms.Form):
    keyword = forms.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., python, web developer, data analyst',
            'required': True
        }),
        help_text='Enter job keywords or job title'
    )
    
    location = forms.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Manila, Cebu, Davao',
            'required': True
        }),
        help_text='Enter city or location'
    )
    
    sources = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text='Select job sources to search (leave empty to search all)'
    )
    
    def __init__(self, *args, **kwargs):
        available_sources = kwargs.pop('available_sources', [('BOSSJOB', 'BossJob.ph')])
        super().__init__(*args, **kwargs)
        self.fields['sources'].choices = available_sources
    
    def clean_keyword(self):
        keyword = self.cleaned_data.get('keyword')
        if keyword:
            # Remove special characters that might break the search
            import re
            keyword = re.sub(r'[^\w\s-]', '', keyword)
            return keyword.strip()
        return keyword
    
    def clean_location(self):
        location = self.cleaned_data.get('location')
        if location:
            # Remove special characters that might break the search
            import re
            location = re.sub(r'[^\w\s-]', '', location)
            return location.strip()
        return location