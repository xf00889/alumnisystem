from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Count, Q
from django.core.exceptions import ValidationError
from .models import Event, EventRSVP
from .forms import EventForm, EventRSVPForm
from alumni_groups.models import AlumniGroup

class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    login_url = 'account_login'

    def get_queryset(self):
        queryset = Event.objects.select_related('created_by').prefetch_related('rsvps')
        
        # Get filter parameters
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        # Annotate with RSVP count
        queryset = queryset.annotate(rsvp_count=Count('rsvps'))
        
        # Order by start date
        return queryset.order_by('start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Get upcoming events
        upcoming_events = Event.objects.filter(
            start_date__gte=now,
            status='published'
        ).order_by('start_date')[:5]
        
        # Get event statistics
        total_events = Event.objects.count()
        published_events = Event.objects.filter(status='published').count()
        upcoming_count = upcoming_events.count()
        past_events = Event.objects.filter(end_date__lt=now).count()
        
        context.update({
            'upcoming_events': upcoming_events,
            'total_events': total_events,
            'published_events': published_events,
            'upcoming_count': upcoming_count,
            'past_events': past_events,
            'total_participants': EventRSVP.objects.filter(status='yes').count(),
            'virtual_events_count': Event.objects.filter(is_virtual=True).count(),
            'search_query': self.request.GET.get('search', ''),
            'current_status': self.request.GET.get('status', ''),
        })
        
        return context

class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_rsvp'] = EventRSVP.objects.filter(
                event=self.object,
                user=self.request.user
            ).first()
            context['rsvp_form'] = EventRSVPForm(instance=context['user_rsvp'])
        context['rsvp_counts'] = {
            'attending': self.object.rsvps.filter(status='yes').count(),
            'not_attending': self.object.rsvps.filter(status='no').count(),
            'maybe': self.object.rsvps.filter(status='maybe').count(),
        }
        return context

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('events:event_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        try:
            # Set the created_by field
            form.instance.created_by = self.request.user
            
            # Save the form
            response = super().form_valid(form)
            
            # Handle notifications for selected groups
            notified_groups = form.cleaned_data.get('notified_groups', [])
            if notified_groups:
                self.object.notified_groups.set(notified_groups)
            
            # Show success message
            messages.success(
                self.request,
                f'Event "{self.object.title}" has been created successfully!'
            )
            
            return response
            
        except ValidationError as e:
            messages.error(self.request, f'Validation error: {str(e)}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error creating event: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Please correct the errors below.'
        )
        return super().form_invalid(form)

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('events:event_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                f'Event "{self.object.title}" has been updated successfully!'
            )
            return response
        except Exception as e:
            messages.error(self.request, f'Error updating event: {str(e)}')
            return self.form_invalid(form)

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    success_url = reverse_lazy('events:event_list')
    template_name = 'events/event_confirm_delete.html'

    def test_func(self):
        return self.request.user.is_staff

@login_required
def event_rsvp(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventRSVPForm(request.POST)
        if form.is_valid():
            rsvp, created = EventRSVP.objects.update_or_create(
                event=event,
                user=request.user,
                defaults={
                    'status': form.cleaned_data['status'],
                    'notes': form.cleaned_data['notes']
                }
            )
            messages.success(request, 'Your RSVP has been recorded.')
        else:
            messages.error(request, 'There was an error with your RSVP.')
    return redirect('events:event_detail', pk=pk)

@login_required
def my_events(request):
    user_rsvps = EventRSVP.objects.filter(user=request.user).select_related('event')
    context = {
        'upcoming_events': [rsvp.event for rsvp in user_rsvps if not rsvp.event.is_past_event],
        'past_events': [rsvp.event for rsvp in user_rsvps if rsvp.event.is_past_event],
    }
    return render(request, 'events/my_events.html', context) 