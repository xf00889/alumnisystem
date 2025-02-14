from django import forms
from .models import Event, EventRSVP
from alumni_groups.models import AlumniGroup

class EventForm(forms.ModelForm):
    notified_groups = forms.ModelMultipleChoiceField(
        queryset=AlumniGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Notify Groups'
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'location', 'is_virtual', 'virtual_link', 'max_participants',
            'status', 'image', 'notified_groups'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_virtual = cleaned_data.get('is_virtual')
        virtual_link = cleaned_data.get('virtual_link')

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")

        if is_virtual and not virtual_link:
            raise forms.ValidationError("Virtual link is required for virtual events.")

        return cleaned_data

class EventRSVPForm(forms.ModelForm):
    class Meta:
        model = EventRSVP
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        } 