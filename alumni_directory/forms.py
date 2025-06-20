from django import forms
from .models import Alumni, AlumniDocument

class AlumniForm(forms.ModelForm):
    class Meta:
        model = Alumni
        exclude = ['user', 'created_at', 'updated_at', 'is_verified', 'is_featured', 'mentorship_status']
        
class AlumniFilterForm(forms.Form):
    graduation_year = forms.MultipleChoiceField(required=False)
    course = forms.MultipleChoiceField(required=False)
    college = forms.MultipleChoiceField(required=False)
    campus = forms.MultipleChoiceField(required=False)
    province = forms.MultipleChoiceField(required=False)
    employment_status = forms.MultipleChoiceField(required=False)
    
    def __init__(self, *args, **kwargs):
        graduation_years = kwargs.pop('graduation_years', [])
        courses = kwargs.pop('courses', [])
        provinces = kwargs.pop('provinces', [])
        super().__init__(*args, **kwargs)
        
        self.fields['graduation_year'].choices = [(year, year) for year in graduation_years]
        self.fields['course'].choices = [(course, course) for course in courses]
        self.fields['province'].choices = [(province, province) for province in provinces]
        self.fields['college'].choices = Alumni.COLLEGE_CHOICES
        self.fields['campus'].choices = Alumni.CAMPUS_CHOICES
        self.fields['employment_status'].choices = Alumni.EMPLOYMENT_STATUS_CHOICES

class AlumniSearchForm(forms.Form):
    search = forms.CharField(required=False)

class AlumniDocumentForm(forms.ModelForm):
    class Meta:
        model = AlumniDocument
        fields = ['title', 'document_type', 'file', 'description'] 