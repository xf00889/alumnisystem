from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    AlumniGroup, GroupEvent, GroupDiscussion,
    GroupDiscussionComment, GroupFile, SecurityQuestion,
    SecurityQuestionAnswer
)

class SecurityQuestionForm(forms.ModelForm):
    class Meta:
        model = SecurityQuestion
        fields = ['question', 'is_required']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class SecurityQuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = SecurityQuestionAnswer
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your answer...'
            })
        }

class SecurityQuestionsFormSet(forms.BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return
        questions = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                question = form.cleaned_data.get('question')
                if question in questions:
                    raise ValidationError('Security questions must be unique.')
                questions.append(question)

class AlumniGroupForm(forms.ModelForm):
    class Meta:
        model = AlumniGroup
        fields = [
            'name', 'description', 'group_type', 'visibility',
            'batch_start_year', 'batch_end_year', 'course', 'campus',
            'requires_approval', 'has_security_questions', 'max_members', 
            'tags', 'cover_image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'group_type': forms.Select(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
            'batch_start_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': timezone.now().year
            }),
            'batch_end_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': timezone.now().year
            }),
            'course': forms.TextInput(attrs={'class': 'form-control'}),
            'campus': forms.Select(attrs={'class': 'form-control'}),
            'max_members': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'data-role': 'tagsinput'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_security_questions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        batch_start = cleaned_data.get('batch_start_year')
        batch_end = cleaned_data.get('batch_end_year')
        
        if batch_start and batch_end and batch_start > batch_end:
            raise ValidationError('Start year must be less than or equal to end year.')
        
        return cleaned_data

class GroupEventForm(forms.ModelForm):
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 'any',
            'data-map-lat': 'true'
        })
    )
    
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 'any',
            'data-map-lng': 'true'
        })
    )
    
    address = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Start typing to search for an address...',
                'data-geocomplete': 'true'
            }
        )
    )

    class Meta:
        model = GroupEvent
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'latitude', 'longitude', 'address', 'is_online', 'meeting_link',
            'max_participants'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker',
                'type': 'datetime-local'
            }),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_online = cleaned_data.get('is_online')
        meeting_link = cleaned_data.get('meeting_link')
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError('Start date must be before end date.')
        
        if is_online and not meeting_link:
            raise ValidationError('Meeting link is required for online events.')
        
        if not is_online and not (latitude and longitude):
            raise ValidationError('Location is required for in-person events.')
        
        return cleaned_data

class GroupDiscussionForm(forms.ModelForm):
    class Meta:
        model = GroupDiscussion
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control rich-text-editor',
                'rows': 6
            })
        }

class GroupDiscussionCommentForm(forms.ModelForm):
    class Meta:
        model = GroupDiscussionComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment...'
            })
        }

class GroupFileForm(forms.ModelForm):
    class Meta:
        model = GroupFile
        fields = ['title', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Add file size validation (e.g., 10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be less than 10MB.')
            
            # Add file type validation
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 
                           'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
            
            if file.content_type not in allowed_types:
                raise ValidationError('Invalid file type. Allowed types: PDF, JPEG, PNG, DOC, DOCX, XLS, XLSX')
        
        return file 