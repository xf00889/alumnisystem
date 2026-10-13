from django import forms
from django.utils import timezone
from .models import MentorCircleMeeting


class MentorCircleMeetingForm(forms.ModelForm):
    class Meta:
        model = MentorCircleMeeting
        fields = ['title', 'meeting_date', 'duration', 'meeting_link', 'agenda']
        widgets = {'meeting_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')}

    def clean_meeting_date(self):
        meeting_date = self.cleaned_data['meeting_date']
        if meeting_date <= timezone.now():
            raise forms.ValidationError('Choose a future meeting date and time.')
        return meeting_date

    def clean_duration(self):
        duration = self.cleaned_data['duration']
        if not 15 <= duration <= 240:
            raise forms.ValidationError('Meeting length must be between 15 and 240 minutes.')
        return duration

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError('Enter a meeting title.')
        return title
