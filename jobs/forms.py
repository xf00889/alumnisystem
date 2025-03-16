from django import forms
from django.forms import inlineformset_factory
from .models import JobPosting, JobApplication, RequiredDocument

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