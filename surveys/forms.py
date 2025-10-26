from django import forms
from django.forms import inlineformset_factory
from django.core.validators import URLValidator
from .models import (
    Survey, SurveyQuestion, QuestionOption, SurveyResponse, 
    ResponseAnswer, EmploymentRecord, Achievement, Report
)
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class SurveyForm(forms.ModelForm):
    external_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://forms.google.com/...'
        }),
        help_text='Enter the URL of your external survey (e.g., Google Forms)'
    )

    class Meta:
        model = Survey
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'external_url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter survey title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter survey description'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'Select start date and time'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'Select end date and time'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_external = self.data.get('is_external') == 'true'
        external_url = cleaned_data.get('external_url')

        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('End date must be after start date')

        if is_external and not external_url:
            raise forms.ValidationError('External URL is required for external surveys')

        return cleaned_data


class SurveyQuestionForm(forms.ModelForm):
    class Meta:
        model = SurveyQuestion
        fields = ['question_text', 'question_type', 'is_required', 'display_order']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 2}),
        }


class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['option_text', 'display_order']


# Create formsets for inline forms
QuestionOptionFormSet = inlineformset_factory(
    SurveyQuestion, 
    QuestionOption,
    form=QuestionOptionForm,
    extra=3,
    can_delete=True
)

SurveyQuestionFormSet = inlineformset_factory(
    Survey,
    SurveyQuestion,
    form=SurveyQuestionForm,
    extra=3,
    can_delete=True
)


class ResponseAnswerForm(forms.ModelForm):
    """
    Base form for response answers that will be extended dynamically
    based on the question type
    """
    class Meta:
        model = ResponseAnswer
        fields = ['question', 'text_answer', 'rating_value', 'selected_option']
        widgets = {
            'question': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
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
        
        if question:
            self.fields['question'].initial = question.id
            self.question_type = question.question_type
            
            # Configure form based on question type
            if question.question_type == 'text':
                self.fields.pop('rating_value')
                self.fields.pop('selected_option')
                self.fields['text_answer'].widget = forms.Textarea(attrs={'rows': 3})
                
            elif question.question_type == 'multiple_choice':
                self.fields.pop('text_answer')
                self.fields.pop('rating_value')
                
                # Create choices from question options
                options = question.options.all()
                self.fields['selected_option'] = forms.ModelChoiceField(
                    queryset=options,
                    widget=forms.RadioSelect(),
                    required=question.is_required
                )
                
            elif question.question_type == 'checkbox':
                self.fields.pop('text_answer')
                self.fields.pop('rating_value')
                self.fields.pop('selected_option')
                
                # Create multiple checkbox fields
                options = question.options.all()
                for option in options:
                    self.fields[f'option_{option.id}'] = forms.BooleanField(
                        label=option.option_text,
                        required=False
                    )
                
            elif question.question_type == 'rating':
                self.fields.pop('text_answer')
                self.fields.pop('selected_option')
                
                # Configure rating field
                self.fields['rating_value'] = forms.IntegerField(
                    min_value=1,
                    max_value=5,
                    widget=forms.NumberInput(attrs={'class': 'rating'}),
                    required=question.is_required
                )
                
            elif question.question_type == 'date':
                self.fields.pop('rating_value')
                self.fields.pop('selected_option')
                self.fields['text_answer'] = forms.DateField(
                    widget=forms.DateInput(attrs={'type': 'date'}),
                    required=question.is_required
                )


class EmploymentRecordForm(forms.ModelForm):
    class Meta:
        model = EmploymentRecord
        fields = ['company_name', 'job_title', 'industry', 'start_date', 
                 'end_date', 'salary_range', 'location']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['title', 'description', 'achievement_date', 'achievement_type']
        widgets = {
            'achievement_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'description', 'report_type', 'parameters']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'parameters': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add dynamic filter fields based on report type
        report_type = self.initial.get('report_type')
        if report_type == 'employment':
            self.fields['industry'] = forms.CharField(required=False)
            self.fields['start_year'] = forms.IntegerField(required=False)
            self.fields['end_year'] = forms.IntegerField(required=False)
            
        elif report_type == 'geographic':
            self.fields['country'] = forms.CharField(required=False)
            self.fields['state'] = forms.CharField(required=False)
            
        elif report_type == 'achievements':
            self.fields['achievement_type'] = forms.ChoiceField(
                choices=[('', '---')] + list(Achievement.ACHIEVEMENT_TYPES),
                required=False
            )
            self.fields['start_date'] = forms.DateField(
                widget=forms.DateInput(attrs={'type': 'date'}),
                required=False
            )
            self.fields['end_date'] = forms.DateField(
                widget=forms.DateInput(attrs={'type': 'date'}),
                required=False
            ) 