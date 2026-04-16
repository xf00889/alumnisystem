from django import forms
from django.forms import inlineformset_factory
from .models import JobPosting, JobApplication, RequiredDocument, JobPreference
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class RequiredDocumentForm(forms.ModelForm):
    class Meta:
        model = RequiredDocument
        fields = ['name', 'document_type', 'description', 'is_required', 'file_types', 'max_file_size']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'max_file_size': forms.NumberInput(attrs={'min': 1, 'step': 1}),  # Size in MB
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['max_file_size'].help_text = "Maximum file size in MB"
        self.fields['file_types'].initial = '.pdf,.doc,.docx'
        self.fields['max_file_size'].initial = 5  # 5MB default

    def clean_max_file_size(self):
        size = self.cleaned_data.get('max_file_size')
        if size:
            # Convert MB to bytes
            return size * 1024 * 1024
        return size

RequiredDocumentFormSet = inlineformset_factory(
    JobPosting,
    RequiredDocument,
    form=RequiredDocumentForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'job_title',
            'company_name',
            'location',
            'job_type',
            'category',
            'source_type',
            'experience_level',
            'job_description',
            'requirements',
            'responsibilities',
            'skills_required',
            'education_requirements',
            'benefits',
            'application_link',
            'salary_range',
            'accepts_internal_applications',
            'is_featured',
            'is_active',
        ]
        widgets = {
            'job_description': forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter job requirements and qualifications...'}),
            'responsibilities': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter key job responsibilities...'}),
            'skills_required': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter required skills (comma-separated)...'}),
            'education_requirements': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter education requirements...'}),
            'benefits': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter job benefits and perks...'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Dumaguete City, Negros Oriental'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'category': 'Industry',
            'location': 'Preferred Location',
        }

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type')
        application_link = cleaned_data.get('application_link')
        accepts_internal_applications = cleaned_data.get('accepts_internal_applications')

        if source_type == 'INTERNAL':
            if not accepts_internal_applications:
                cleaned_data['accepts_internal_applications'] = True
        elif source_type == 'EXTERNAL' and not application_link and not accepts_internal_applications:
            self.add_error('application_link', 'External positions must have either an application link or accept internal applications.')

        return cleaned_data

    def clean_application_link(self):
        url = self.cleaned_data.get('application_link')
        if url:  # Only process if URL is not empty
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return url
        return url  # Return None/empty value if no URL provided

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'cover_letter',
            'resume',
            'additional_documents',
        ]
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Write a brief cover letter explaining why you are interested in this position...'
            }),
        }

    def __init__(self, *args, job=None, **kwargs):
        super().__init__(*args, **kwargs)
        if job:
            required_docs = job.required_documents.filter(is_required=True)
            if required_docs.exists():
                for doc in required_docs:
                    field_name = f'document_{doc.id}'
                    self.fields[field_name] = forms.FileField(
                        label=doc.name,
                        help_text=f"{doc.description} (Allowed types: {doc.file_types})",
                        required=True
                    )
        
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

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if not resume:
            raise forms.ValidationError('A resume is required.')
        if resume.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError('Resume file size must be under 5MB.')
        return resume

    def clean_additional_documents(self):
        documents = self.cleaned_data.get('additional_documents')
        if documents and documents.size > 10 * 1024 * 1024:  # 10MB limit
            raise forms.ValidationError('Additional documents file size must be under 10MB.')
        return documents 


class JobPreferenceForm(forms.ModelForm):
    """Form for job preference configuration"""
    
    class Meta:
        model = JobPreference
        fields = [
            'job_types',
            'industries',
            'location_text',
            'remote_only',
            'willing_to_relocate',
            'experience_levels',
            'minimum_salary',
            'source_type',
            'skill_matching_enabled',
            'skill_match_threshold',
        ]
        widgets = {
            'job_types': forms.CheckboxSelectMultiple(
                choices=JobPosting.JOB_TYPE_CHOICES
            ),
            'industries': forms.CheckboxSelectMultiple(
                choices=JobPosting.CATEGORY_CHOICES
            ),
            'experience_levels': forms.CheckboxSelectMultiple(
                choices=JobPosting.EXPERIENCE_LEVEL_CHOICES
            ),
            'location_text': forms.TextInput(attrs={
                'placeholder': 'e.g., Dumaguete, Cebu, Manila',
                'class': 'form-control'
            }),
            'remote_only': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'willing_to_relocate': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'minimum_salary': forms.NumberInput(attrs={
                'placeholder': 'e.g., 20000',
                'class': 'form-control',
                'min': 0
            }),
            'source_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'skill_matching_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'skill_match_threshold': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'class': 'form-control'
            }),
        }
    
    def clean_skill_match_threshold(self):
        """Validate threshold is between 0-100"""
        threshold = self.cleaned_data.get('skill_match_threshold')
        if threshold is not None and (threshold < 0 or threshold > 100):
            raise forms.ValidationError("Threshold must be between 0 and 100")
        return threshold
    
    def clean_job_types(self):
        """Validate job types against JobPosting.JOB_TYPE_CHOICES"""
        job_types = self.cleaned_data.get('job_types')
        
        if not job_types:
            return job_types
        
        # Get valid job type values from JobPosting choices
        valid_job_types = [choice[0] for choice in JobPosting.JOB_TYPE_CHOICES]
        
        # Validate each selected job type
        invalid_types = [jt for jt in job_types if jt not in valid_job_types]
        
        if invalid_types:
            raise forms.ValidationError(
                f"Invalid job type(s): {', '.join(invalid_types)}. "
                f"Valid options are: {', '.join(valid_job_types)}"
            )
        
        return job_types
    
    def clean_industries(self):
        """Validate industries against JobPosting.CATEGORY_CHOICES"""
        industries = self.cleaned_data.get('industries')
        
        if not industries:
            return industries
        
        # Get valid industry/category values from JobPosting choices
        valid_industries = [choice[0] for choice in JobPosting.CATEGORY_CHOICES]
        
        # Validate each selected industry
        invalid_industries = [ind for ind in industries if ind not in valid_industries]
        
        if invalid_industries:
            raise forms.ValidationError(
                f"Invalid industry/category: {', '.join(invalid_industries)}. "
                f"Valid options are: {', '.join(valid_industries)}"
            )
        
        return industries
    
    def clean_experience_levels(self):
        """Validate experience levels against JobPosting.EXPERIENCE_LEVEL_CHOICES"""
        experience_levels = self.cleaned_data.get('experience_levels')
        
        if not experience_levels:
            return experience_levels
        
        # Get valid experience level values from JobPosting choices
        valid_levels = [choice[0] for choice in JobPosting.EXPERIENCE_LEVEL_CHOICES]
        
        # Validate each selected experience level
        invalid_levels = [level for level in experience_levels if level not in valid_levels]
        
        if invalid_levels:
            raise forms.ValidationError(
                f"Invalid experience level(s): {', '.join(invalid_levels)}. "
                f"Valid options are: {', '.join(valid_levels)}"
            )
        
        return experience_levels
    
    def clean_minimum_salary(self):
        """Validate minimum salary is a positive integer"""
        minimum_salary = self.cleaned_data.get('minimum_salary')
        
        # Allow None/blank values (field is optional)
        if minimum_salary is None:
            return minimum_salary
        
        # Ensure it's a positive integer
        if minimum_salary < 0:
            raise forms.ValidationError("Minimum salary must be a positive number")
        
        return minimum_salary
