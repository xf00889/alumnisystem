from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib import messages
from .models import Announcement, Category
from .forms import AnnouncementForm, AnnouncementUpdateForm, PublicAnnouncementForm
from .utils import send_announcement_notification
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_deny
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.html import escape
from django.utils.text import normalize_newlines
from django.http import JsonResponse
from django.template.loader import render_to_string

# Create your views here.

# Public views for non-registered users
@method_decorator([
    csrf_protect,
    cache_control(public=True, max_age=300),
    xframe_options_deny,
], name='dispatch')
class PublicAnnouncementListView(ListView):
    model = Announcement
    template_name = 'announcements/public_announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10
    
    def get_queryset(self):
        # Only show active announcements with ALL target audience for public view
        queryset = Announcement.objects.filter(
            is_active=True, 
            target_audience='ALL'
        ).order_by('-date_posted')
        
        # Apply search filter
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        # Apply category filter
        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category__id__in=categories)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        
        # Add filter state to context
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_categories'] = [int(cat) for cat in self.request.GET.getlist('category')]
        context['is_public_view'] = True
        
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # For AJAX requests, return only the announcement list and pagination
            context = self.get_context_data()
            html = render_to_string('announcements/_announcement_list.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': context['page_obj'].has_next(),
                'has_previous': context['page_obj'].has_previous(),
                'page': context['page_obj'].number,
                'total_pages': context['paginator'].num_pages,
            })
            
        return response

@method_decorator([
    csrf_protect,
    cache_control(public=True, max_age=300),
    xframe_options_deny,
], name='dispatch')
class PublicAnnouncementDetailView(DetailView):
    model = Announcement
    template_name = 'announcements/public_announcement_detail.html'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # For public view, only show active announcements with ALL target audience
        if not obj.is_active or obj.target_audience != 'ALL':
            raise PermissionDenied("This announcement is not available for public view.")
        obj.views_count += 1
        obj.save()
        return obj

@method_decorator([
    csrf_protect,
    cache_control(private=True, no_cache=True, no_store=True, must_revalidate=True),
    xframe_options_deny,
], name='dispatch')
class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Announcement.objects.filter(is_active=True).order_by('-date_posted')
        
        # Apply search filter
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        # Apply category filter
        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category__id__in=categories)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        
        # Add filter state to context
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_categories'] = [int(cat) for cat in self.request.GET.getlist('category')]
        
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # For AJAX requests, return only the announcement list and pagination
            context = self.get_context_data()
            html = render_to_string('announcements/_announcement_list.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': context['page_obj'].has_next(),
                'has_previous': context['page_obj'].has_previous(),
                'page': context['page_obj'].number,
                'total_pages': context['paginator'].num_pages,
            })
            
        return response

@method_decorator([
    csrf_protect,
    cache_control(private=True),
    xframe_options_deny,
], name='dispatch')
class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'announcements/announcement_detail.html'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_visible_to(self.request.user):
            raise PermissionDenied("You don't have permission to view this announcement.")
        obj.views_count += 1
        obj.save()
        return obj

@method_decorator([
    csrf_protect,
    cache_control(private=True, no_cache=True, no_store=True, must_revalidate=True),
    xframe_options_deny,
], name='dispatch')
class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_message = "Announcement was created successfully!"
    success_url = reverse_lazy('announcements:announcement-list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to perform this action.")
        return redirect('announcements:announcement-list')

    def form_valid(self, form):
        # Sanitize user input
        form.instance.title = escape(form.instance.title)
        # Normalize newlines and escape content, then convert newlines to <br>
        content = escape(normalize_newlines(form.instance.content))
        form.instance.content = content.replace('\n', '<br>')
        
        # No need to modify category handling as the form will properly set
        # the category based on the selected predefined option
        
        response = super().form_valid(form)
        # Send email notification
        if send_announcement_notification(self.object):
            messages.success(self.request, "Email notifications have been sent successfully.")
        else:
            messages.warning(self.request, "The announcement was created but there was an error sending email notifications.")
        return response

@method_decorator([
    csrf_protect,
    cache_control(private=True, no_cache=True, no_store=True, must_revalidate=True),
    xframe_options_deny,
], name='dispatch')
class AnnouncementUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementUpdateForm
    template_name = 'announcements/announcement_form.html'
    success_message = "Announcement was updated successfully!"
    success_url = reverse_lazy('announcements:announcement-list')
    
    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_staff

    def form_valid(self, form):
        # Sanitize user input
        form.instance.title = escape(form.instance.title)
        # Normalize newlines and escape content, then convert newlines to <br>
        content = escape(normalize_newlines(form.instance.content))
        form.instance.content = content.replace('\n', '<br>')
        
        # No need to modify category handling as the form will properly set
        # the category based on the selected predefined option
        
        return super().form_valid(form)

@method_decorator([
    csrf_protect,
    cache_control(private=True, no_cache=True, no_store=True, must_revalidate=True),
    xframe_options_deny,
], name='dispatch')
class AnnouncementDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Announcement
    success_url = reverse_lazy('announcements:announcement-list')
    
    def test_func(self):
        """Check if user is staff or superuser"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request, *args, **kwargs):
        """Block GET requests - deletion should only happen via POST with AJAX"""
        messages.error(request, 'Invalid request. Please use the delete button to delete announcements.')
        return redirect('announcements:announcement-list')

    def post(self, request, *args, **kwargs):
        """Override post to handle both AJAX and regular requests"""
        # Check permissions first
        if not (request.user.is_staff or request.user.is_superuser):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'You do not have permission to delete announcements.'
                }, status=403)
            messages.error(request, 'You do not have permission to delete announcements.')
            return redirect('announcements:announcement-list')
        
        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            
            # Clear cache before deletion
            cache.delete('announcement_list')
            cache.delete(f'announcement_{self.object.pk}')
            cache.delete(f'announcement_card_{self.object.pk}')
            
            # Delete the announcement
            self.object.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Announcement was deleted successfully.'
                })
            
            messages.success(request, 'Announcement was deleted successfully.')
            return redirect(success_url)
            
        except PermissionDenied as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e) or "You don't have permission to perform this action."
                }, status=403)
            raise
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error deleting announcement: {str(e)}'
                }, status=500)
            messages.error(request, f'Error deleting announcement: {str(e)}')
            return redirect(success_url)

    def handle_no_permission(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': "You don't have permission to perform this action."
            }, status=403)
        messages.error(self.request, "You don't have permission to perform this action.")
        return redirect('announcements:announcement-list')

def announcement_search(request):
    try:
        query = request.GET.get('q', '').strip()
        categories = request.GET.getlist('category')

        # Build the base queryset
        queryset = Announcement.objects.filter(is_active=True).order_by('-date_posted')

        # Apply search filter if query exists
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(category__name__icontains=query)
            )

        # Apply category filter if categories are selected
        if categories:
            categories = [cat for cat in categories if cat]  # Remove empty strings
            if categories:
                queryset = queryset.filter(category__id__in=categories)

        # Render the template with the filtered queryset
        html = render_to_string('announcements/_announcement_list.html', {
            'announcements': queryset,
            'request': request
        })

        # Return JSON response
        return JsonResponse({
            'status': 'success',
            'html': html,
            'count': queryset.count()
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@method_decorator([
    csrf_protect,
    cache_control(private=True, no_cache=True, no_store=True, must_revalidate=True),
    xframe_options_deny,
], name='dispatch')
class PublicAnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Announcement
    form_class = PublicAnnouncementForm
    template_name = 'announcements/public_announcement_form.html'
    success_message = "Public announcement was created successfully!"
    success_url = reverse_lazy('announcements:public-announcement-list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to perform this action.")
        return redirect('announcements:public-announcement-list')

    def form_valid(self, form):
        # Sanitize user input
        form.instance.title = escape(form.instance.title)
        # Normalize newlines and escape content, then convert newlines to <br>
        content = escape(normalize_newlines(form.instance.content))
        form.instance.content = content.replace('\n', '<br>')
        
        # Force target audience to "ALL" for public announcements
        form.instance.target_audience = 'ALL'
        form.instance.is_active = True
        
        response = super().form_valid(form)
        # Send email notification
        if send_announcement_notification(self.object):
            messages.success(self.request, "Email notifications have been sent successfully.")
        else:
            messages.warning(self.request, "The announcement was created but there was an error sending email notifications.")
        return response
