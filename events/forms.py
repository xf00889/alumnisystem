from django import forms
from .models import Event, EventRSVP
from alumni_groups.models import AlumniGroup
from django.utils import timezone

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
            'start_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert datetime to local format for form fields
        if self.instance.pk:
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_virtual = cleaned_data.get('is_virtual')
        virtual_link = cleaned_data.get('virtual_link')
        location = cleaned_data.get('location')
        status = cleaned_data.get('status')

        if start_date:
            if start_date < timezone.now():
                self.add_error('start_date', "Start date cannot be in the past.")

        if start_date and end_date:
            if end_date <= start_date:
                self.add_error('end_date', "End date must be after start date.")

        if is_virtual:
            if not virtual_link:
                self.add_error('virtual_link', "Virtual link is required for virtual events.")
            if location and location != 'Virtual Event':
                cleaned_data['location'] = 'Virtual Event'
        else:
            if not location:
                self.add_error('location', "Location is required for in-person events.")
            cleaned_data['virtual_link'] = None

        if status == 'published':
            if not all([start_date, end_date, location or (is_virtual and virtual_link)]):
                raise forms.ValidationError(
                    "Cannot publish event without all required fields: start date, end date, and location/virtual link."
                )

        return cleaned_data

class EventRSVPForm(forms.ModelForm):
    class Meta:
        model = EventRSVP
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        } 