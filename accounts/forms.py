from django import forms
from django.forms import inlineformset_factory
from .models import (
    Profile, Education, Experience, Skill, Document,
    MentorApplication, Mentor
)
from django.contrib.auth.models import User
from alumni_directory.models import Alumni
import datetime
from django_countries.fields import CountryField
from django_countries import countries
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
        # Create profile if it doesn't exist
        Profile.objects.get_or_create(user=user)
        
        return user

class PostRegistrationForm(forms.Form):
    PROGRAM_CHOICES = [
        ('', '-- Select your program --'),
        # College of Arts and Sciences (CAS)
        ('BSIT', 'BS in Information Technology'),
        ('BSCS', 'BS in Computer Science'),
        ('BSP', 'BS in Psychology'),
        ('BSM', 'BS in Mathematics'),
        ('BSPHY', 'BS in Physics'),
        ('BSBIO', 'BS in Biology'),
        # College of Business Administration (CBA)
        ('BSA', 'BS in Accountancy'),
        ('BSBA-FM', 'BSBA in Financial Management'),
        ('BSBA-MM', 'BSBA in Marketing Management'),
        ('BSBA-HRM', 'BSBA in Human Resource Management'),
        # College of Teacher Education (CTE)
        ('BEED', 'Bachelor of Elementary Education'),
        ('BSED-ENG', 'BS in Education - English'),
        ('BSED-MATH', 'BS in Education - Mathematics'),
        ('BSED-SCI', 'BS in Education - Science'),
        ('BSED-SS', 'BS in Education - Social Studies'),
        # College of Nursing, Pharmacy and Allied Health Sciences (CNPAHS)
        ('BSN', 'BS in Nursing'),
        ('BSP', 'BS in Pharmacy'),
        ('BSMT', 'BS in Medical Technology'),
        # College of Criminal Justice Education (CCJE)
        ('BSCRIM', 'BS in Criminology'),
        # College of Tourism and Hospitality Management (CTHM)
        ('BSHRM', 'BS in Hotel and Restaurant Management'),
        ('BSTM', 'BS in Tourism Management'),
        # College of Engineering and Architecture (CEA)
        ('BSCE', 'BS in Civil Engineering'),
        ('BSEE', 'BS in Electrical Engineering'),
        ('BSME', 'BS in Mechanical Engineering'),
        ('BSARCH', 'BS in Architecture'),
        # College of Agriculture, Forestry and Fishery (CAFF)
        ('BSA-AGRI', 'BS in Agriculture'),
        ('BSF', 'BS in Forestry'),
        ('BSFT', 'BS in Fisheries Technology'),
        # College of Industrial Technology (CIT)
        ('BSIT-AT', 'BS in Industrial Technology - Automotive'),
        ('BSIT-ET', 'BS in Industrial Technology - Electronics'),
        ('BSIT-FPSM', 'BS in Industrial Technology - Food Processing'),
        ('OTHER', 'Other Program'),
    ]

    SCHOOL_CHOICES = [
        ('', '-- Select your campus --'),
        ('NORSU-MAIN', 'Main Campus I & II (Dumaguete)'),
        ('NORSU-BAIS', 'Bais Campus I & II'),
        ('NORSU-GUI', 'Guihulngan Campus'),
        ('NORSU-MAB', 'Mabinay Campus'),
        ('NORSU-BSC', 'Bayawan-Sta. Catalina Campus'),
        ('NORSU-SIA', 'Siaton Campus'),
        ('NORSU-PAM', 'Pamplona Campus'),
        ('OTHER', 'Other Campus'),
    ]

    GENDER_CHOICES = [
        ('', '-- Select your gender --'),
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        help_text="Enter your first name as it appears on your diploma"
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text="Enter your last name as it appears on your diploma"
    )
    graduation_year = forms.IntegerField(
        required=True,
        min_value=1970,
        max_value=datetime.datetime.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY',
            'min': 1970,
            'max': datetime.datetime.now().year
        }),
        help_text="Year you graduated",
        label="Year"
    )
    course_graduated = forms.ChoiceField(
        choices=PROGRAM_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Program you completed",
        label="Course Graduated"
    )
    present_occupation = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current job title'
        }),
        help_text="Your current job title or position"
    )
    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current company'
        }),
        help_text="The name of the company you currently work for"
    )
    employment_address = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your workplace address',
            'rows': 3
        }),
        help_text="Address of your current employment"
    )

    def clean_graduation_year(self):
        year = self.cleaned_data['graduation_year']
        current_year = datetime.datetime.now().year
        if year < 1970 or year > current_year:
            raise forms.ValidationError(f"Please enter a year between 1970 and {current_year}")
        return year

    def save(self, user):
        # Update user's first and last name
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Create or update primary education record
        Education.objects.update_or_create(
            profile=user.profile,
            is_primary=True,
            defaults={
                'program': self.cleaned_data['course_graduated'],
                'graduation_year': self.cleaned_data['graduation_year'],
            }
        )

        # Update user's profile with employment information
        profile = user.profile
        profile.current_position = self.cleaned_data['present_occupation']
        profile.current_employer = self.cleaned_data['company_name']
        profile.address = self.cleaned_data['employment_address']
        profile.has_completed_registration = True
        profile.save()

        # Create current employment experience
        import datetime
        current_exp = Experience.objects.create(
            profile=profile,
            position=self.cleaned_data['present_occupation'],
            company=self.cleaned_data['company_name'],
            location=self.cleaned_data['employment_address'],
            start_date=datetime.date.today(),
            is_current=True,
            career_significance='REGULAR'
        )

        # Create or update Alumni record
        Alumni.objects.update_or_create(
            user=user,
            defaults={
                'graduation_year': self.cleaned_data['graduation_year'],
                'course': self.cleaned_data['course_graduated'],
                'current_company': self.cleaned_data['company_name'],
                'job_title': self.cleaned_data['present_occupation'],
                'address': self.cleaned_data['employment_address'],
                'employment_status': 'EMPLOYED_FULL'  # Assuming full-time employment
            }
        )

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        help_text="Enter your first name"
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        help_text="Enter your last name"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        help_text="Upload a profile picture (JPG, PNG, GIF). Max size: 5MB"
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False,
        help_text="Tell us about yourself"
    )
    country = forms.ChoiceField(
        choices=[('', 'Select Country')] + list(countries),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profile
        fields = [
            'avatar',
            'bio',
            'birth_date',
            'gender',
            'phone_number',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'linkedin_profile',
            'facebook_profile',
            'twitter_profile',
            'current_position',
            'current_employer',
            'industry',
            'employment_status',
            'salary_range',
            'is_public'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'current_position': forms.TextInput(attrs={'placeholder': 'e.g. Software Engineer'}),
            'current_employer': forms.TextInput(attrs={'placeholder': 'e.g. Tech Company Inc.'}),
            'industry': forms.TextInput(attrs={'placeholder': 'e.g. Information Technology'}),
        }
        labels = {
            'current_position': 'Current Position',
            'current_employer': 'Current Employer',
            'industry': 'Industry',
            'employment_status': 'Employment Status',
            'salary_range': 'Salary Range',
        }
        help_texts = {
            'salary_range': 'This information will be kept private and used for statistical purposes only.',
            'employment_status': 'Select your current employment status',
            'industry': 'Enter the industry you currently work in',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields not required
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        # Clean URLs - ensure they have http:// or https:// prefix
        for field in ['linkedin_profile', 'facebook_profile', 'twitter_profile']:
            url = cleaned_data.get(field)
            if url and not url.startswith(('http://', 'https://')):
                cleaned_data[field] = f'https://{url}'
        return cleaned_data

class EducationForm(forms.ModelForm):
    program = forms.ChoiceField(
        choices=Education.PROGRAM_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    school = forms.ChoiceField(
        choices=Education.SCHOOL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    graduation_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Education
        fields = ['program', 'major', 'school', 'graduation_year', 'achievements']
        widgets = {
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        help_texts = {
            'program': 'Your program',
            'major': 'Your specialization (if any)',
            'school': 'Your campus',
            'graduation_year': 'Year of graduation',
            'achievements': 'Notable achievements, awards, or honors'
        }

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            'company', 'position', 'location', 'start_date', 'end_date', 
            'is_current', 'description', 'career_significance', 
            'achievements', 'salary_range', 'skills_gained'
        ]
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'career_significance': forms.Select(attrs={'class': 'form-select'}),
            'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control'}),
            'skills_gained': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
        help_texts = {
            'is_current': 'Check this if this is your current job. This will update your profile\'s current position.',
            'skills_gained': 'Enter skills gained in this role, separated by commas.',
            'achievements': 'List your key achievements in this role.',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')

        if is_current:
            cleaned_data['end_date'] = None
        elif start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be earlier than start date.")

        return cleaned_data

class SkillForm(forms.ModelForm):
    skill_type = forms.ChoiceField(
        choices=[('', '---------')] + list(Skill.SKILL_TYPES),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select skill type'
        })
    )
    proficiency_level = forms.ChoiceField(
        choices=[('', '---------')] + list(Skill.PROFICIENCY_LEVELS),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select proficiency level'
        })
    )
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter skill name'
        })
    )
    
    class Meta:
        model = Skill
        fields = ['name', 'skill_type', 'proficiency_level']
        help_texts = {
            'name': 'Name of the skill',
            'skill_type': 'Category of the skill',
            'proficiency_level': 'Rate your proficiency from 1 to 5'
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        skill_type = cleaned_data.get('skill_type')
        proficiency_level = cleaned_data.get('proficiency_level')

        if not name and (skill_type or proficiency_level):
            raise forms.ValidationError("Skill name is required if type or proficiency is specified.")
        
        if name and not skill_type:
            raise forms.ValidationError("Please select a skill type.")
            
        if name and not proficiency_level:
            raise forms.ValidationError("Please select a proficiency level.")

        return cleaned_data

class DocumentUploadForm(forms.ModelForm):
    title = forms.CharField(
        max_length=255,
        required=False,
        help_text="Give your document a descriptive title"
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.doc,.docx'
        }),
        help_text="Upload PDF, DOC, or DOCX files (Max size: 5MB)"
    )

    class Meta:
        model = Document
        fields = ['title', 'file']

class TranscriptUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'TRANSCRIPT'
        self.fields['title'].help_text = "Name of your academic transcript"
        self.fields['file'].help_text = "Upload your academic transcript (PDF format preferred)"

class CertificateUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'CERTIFICATE'
        self.fields['title'].help_text = "Name of your certificate"
        self.fields['file'].help_text = "Upload your certificate (PDF format preferred)"

class DiplomaUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'DIPLOMA'
        self.fields['title'].help_text = "Name of your diploma"
        self.fields['file'].help_text = "Upload your diploma (PDF format preferred)"

class ResumeUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'RESUME'
        self.fields['title'].help_text = "Name your resume/CV"
        self.fields['file'].help_text = "Upload your resume/CV (PDF format preferred)"

# Create formsets for related models
EducationFormSet = inlineformset_factory(
    Profile,
    Education,
    form=EducationForm,
    extra=1,
    can_delete=True,
    fields=['program', 'major', 'school', 'graduation_year', 'achievements'],
    widgets={
        'major': forms.TextInput(attrs={'class': 'form-control'}),
        'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
    }
)

ExperienceFormSet = inlineformset_factory(
    Profile,
    Experience,
    form=ExperienceForm,
    extra=1,
    can_delete=True,
    fields=[
        'company', 'position', 'location', 'start_date', 'end_date', 
        'is_current', 'description', 'career_significance', 
        'achievements', 'salary_range', 'skills_gained'
    ],
    widgets={
        'company': forms.TextInput(attrs={'class': 'form-control'}),
        'position': forms.TextInput(attrs={'class': 'form-control'}),
        'location': forms.TextInput(attrs={'class': 'form-control'}),
        'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        'career_significance': forms.Select(attrs={'class': 'form-select'}),
        'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        'salary_range': forms.TextInput(attrs={'class': 'form-control'}),
        'skills_gained': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
    }
)

SkillFormSet = inlineformset_factory(
    Profile,
    Skill,
    form=SkillForm,
    extra=1,
    can_delete=True,
    validate_min=False,
    fields=['name', 'skill_type', 'proficiency_level']
)

class MentorApplicationForm(forms.ModelForm):
    expertise_areas = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your areas of expertise (comma-separated)'
        }),
        help_text='List your areas of expertise, separated by commas'
    )
    
    years_of_experience = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Years of professional experience'
        })
    )
    
    certifications = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        }),
        help_text='Upload your certifications in PDF format'
    )
    
    training_documents = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        }),
        help_text='Upload your training documents in PDF format'
    )
    
    competency_summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe your expertise and competencies'
        }),
        help_text='Provide a detailed summary of your expertise and how you can help mentees'
    )
    
    class Meta:
        model = MentorApplication
        fields = ['expertise_areas', 'years_of_experience', 'certifications', 'training_documents', 'competency_summary']
        
    def clean_certifications(self):
        certifications = self.cleaned_data.get('certifications')
        if certifications:
            if not certifications.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed for certifications.')
            if certifications.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('File size must be under 5MB.')
        return certifications
    
    def clean_training_documents(self):
        training_docs = self.cleaned_data.get('training_documents')
        if training_docs:
            if not training_docs.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed for training documents.')
            if training_docs.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('File size must be under 5MB.')
        return training_docs 