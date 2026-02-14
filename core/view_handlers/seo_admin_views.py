"""
SEO Management Views for Admin Dashboard

Provides comprehensive SEO configuration management including:
- PageSEO listing with search and filtering
- PageSEO creation and editing
- PageSEO deletion
- OrganizationSchema editing
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator

from core.mixins import SuperuserRequiredMixin, StaffRequiredMixin
from core.models.seo import PageSEO, OrganizationSchema
from core.forms import PageSEOForm, OrganizationSchemaForm

import logging

logger = logging.getLogger('core')


class PageSEOListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    List all PageSEO entries with search and filtering capabilities.
    
    Features:
    - Search by page path or meta title
    - Filter by active status
    - Pagination (20 entries per page)
    - Character count indicators
    
    Requirements: 13.1
    """
    
    model = PageSEO
    template_name = 'admin/seo/page_seo_list.html'
    context_object_name = 'page_seos'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Build queryset with search and filtering applied.
        """
        queryset = PageSEO.objects.all().order_by('page_path')
        
        # Get filter parameters
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        
        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(page_path__icontains=search_query) |
                Q(meta_title__icontains=search_query) |
                Q(meta_description__icontains=search_query)
            )
        
        # Apply status filter
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add search parameters and counts to context.
        """
        context = super().get_context_data(**kwargs)
        
        # Add current filter values for UI state
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        # Add status counts for UI badges
        context['status_counts'] = {
            'total': PageSEO.objects.count(),
            'active': PageSEO.objects.filter(is_active=True).count(),
            'inactive': PageSEO.objects.filter(is_active=False).count(),
        }
        
        # Add permission flags for UI
        context['is_superuser'] = self.request.user.is_superuser
        context['can_create'] = self.request.user.is_superuser or self.request.user.is_staff
        context['can_modify'] = self.request.user.is_superuser or self.request.user.is_staff
        
        return context


class PageSEOCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    Create a new PageSEO entry.
    
    Features:
    - Form validation for character counts
    - Success/error messages
    - Redirects to list view on success
    
    Requirements: 13.1, 13.4, 13.5
    """
    
    model = PageSEO
    form_class = PageSEOForm
    template_name = 'admin/seo/page_seo_form.html'
    success_url = reverse_lazy('core:seo_page_list')
    
    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        try:
            response = super().form_valid(form)
            
            messages.success(
                self.request,
                f'SEO configuration created successfully for {self.object.page_path}.'
            )
            
            logger.info(
                f"PageSEO created for {self.object.page_path} by {self.request.user.email}",
                extra={
                    'page_seo_id': self.object.id,
                    'page_path': self.object.page_path,
                    'created_by': self.request.user.email,
                    'action': 'page_seo_created'
                }
            )
            
            return response
        except Exception as e:
            messages.error(
                self.request,
                f'Failed to create SEO configuration: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        messages.error(
            self.request,
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add additional context for template"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create SEO Configuration'
        context['submit_button_text'] = 'Create Configuration'
        context['is_edit'] = False
        return context


class PageSEOEditView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    Edit an existing PageSEO entry.
    
    Features:
    - Form validation for character counts
    - Success/error messages
    - Redirects to list view on success
    
    Requirements: 13.1, 13.2, 13.4, 13.5
    """
    
    model = PageSEO
    form_class = PageSEOForm
    template_name = 'admin/seo/page_seo_form.html'
    success_url = reverse_lazy('core:seo_page_list')
    
    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        try:
            response = super().form_valid(form)
            
            messages.success(
                self.request,
                f'SEO configuration updated successfully for {self.object.page_path}.'
            )
            
            logger.info(
                f"PageSEO updated for {self.object.page_path} by {self.request.user.email}",
                extra={
                    'page_seo_id': self.object.id,
                    'page_path': self.object.page_path,
                    'updated_by': self.request.user.email,
                    'action': 'page_seo_updated'
                }
            )
            
            return response
        except Exception as e:
            messages.error(
                self.request,
                f'Failed to update SEO configuration: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        messages.error(
            self.request,
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add additional context for template"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit SEO Configuration - {self.object.page_path}'
        context['submit_button_text'] = 'Update Configuration'
        context['is_edit'] = True
        return context


class PageSEODeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    """
    Delete a PageSEO entry.
    
    Features:
    - Confirmation page
    - Success/error messages
    - Redirects to list view on success
    
    Requirements: 13.1
    """
    
    model = PageSEO
    template_name = 'admin/seo/page_seo_delete.html'
    success_url = reverse_lazy('core:seo_page_list')
    
    def delete(self, request, *args, **kwargs):
        """
        Handle delete request.
        """
        page_path = self.get_object().page_path
        
        try:
            response = super().delete(request, *args, **kwargs)
            
            messages.success(
                request,
                f'SEO configuration deleted successfully for {page_path}.'
            )
            
            logger.info(
                f"PageSEO deleted for {page_path} by {request.user.email}",
                extra={
                    'page_path': page_path,
                    'deleted_by': request.user.email,
                    'action': 'page_seo_deleted'
                }
            )
            
            return response
        except Exception as e:
            messages.error(
                request,
                f'Failed to delete SEO configuration: {str(e)}'
            )
            return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """Add additional context for template"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Delete SEO Configuration - {self.object.page_path}'
        return context


class OrganizationSchemaEditView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    Edit the OrganizationSchema entry.
    
    Features:
    - Form validation for email and URLs
    - Success/error messages
    - Redirects to list view on success
    - Creates entry if none exists
    
    Requirements: 13.1
    """
    
    model = OrganizationSchema
    form_class = OrganizationSchemaForm
    template_name = 'admin/seo/organization_schema_form.html'
    success_url = reverse_lazy('core:seo_page_list')
    
    def get_object(self, queryset=None):
        """
        Get the active OrganizationSchema or create a new one.
        """
        try:
            return OrganizationSchema.objects.filter(is_active=True).first() or OrganizationSchema()
        except OrganizationSchema.DoesNotExist:
            return OrganizationSchema()
    
    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        try:
            # Deactivate all other organization schemas
            OrganizationSchema.objects.all().update(is_active=False)
            
            # Save the current one as active
            form.instance.is_active = True
            response = super().form_valid(form)
            
            messages.success(
                self.request,
                f'Organization schema updated successfully for {self.object.name}.'
            )
            
            logger.info(
                f"OrganizationSchema updated for {self.object.name} by {self.request.user.email}",
                extra={
                    'organization_schema_id': self.object.id,
                    'organization_name': self.object.name,
                    'updated_by': self.request.user.email,
                    'action': 'organization_schema_updated'
                }
            )
            
            return response
        except Exception as e:
            messages.error(
                self.request,
                f'Failed to update organization schema: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        messages.error(
            self.request,
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add additional context for template"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Organization Schema'
        context['submit_button_text'] = 'Update Schema'
        return context
