from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Count
from .models import Event, EventRSVP
from .forms import EventForm, EventRSVPForm
from alumni_groups.models import AlumniGroup

class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 10
    login_url = 'account_login'

    def get_queryset(self):
        queryset = Event.objects.annotate(rsvp_count=Count('rsvps'))
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upcoming_events'] = Event.objects.filter(
            start_date__gte=timezone.now(),
            status='published'
        ).order_by('start_date')[:5]
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
    success_url = reverse_lazy('events:event_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Handle notifications for selected groups
        notified_groups = form.cleaned_data.get('notified_groups', [])
        if notified_groups:
            self.object.notified_groups.set(notified_groups)
            # Here you would add logic to send notifications to group members
            
        messages.success(self.request, 'Event created successfully!')
        return response

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy('events:event_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Event updated successfully!')
        return response

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