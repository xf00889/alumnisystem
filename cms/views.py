from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import (
    SiteConfig, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial,
    AlumniStatistic, NORSUVMGOHistory
)
from .forms import (
    SiteConfigForm, HeroSectionForm, StaffMemberForm,
    TimelineItemForm, ContactInfoForm, FAQForm, FeatureForm, TestimonialForm,
    AlumniStatisticForm, VMGOSectionForm
)


@method_decorator(login_required, name='dispatch')
class CMSDashboardView(TemplateView):
    """
    CMS Dashboard - Central hub for managing all CMS content
    """
    template_name = 'cms/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts for dashboard statistics
        context.update({
            'site_config_count': SiteConfig.objects.count(),
            'staff_members_count': StaffMember.objects.filter(is_active=True).count(),
            'timeline_items_count': TimelineItem.objects.filter(is_active=True).count(),
            'contact_info_count': ContactInfo.objects.filter(is_active=True).count(),
            'faqs_count': FAQ.objects.filter(is_active=True).count(),
            'features_count': Feature.objects.filter(is_active=True).count(),
            'testimonials_count': Testimonial.objects.filter(is_active=True).count(),
            'alumni_statistics_count': AlumniStatistic.objects.filter(is_active=True).count(),
        })
        
        # Get recent content for quick access
        context.update({
            'recent_faqs': FAQ.objects.filter(is_active=True).order_by('-modified')[:5],
        })
        
        return context


# Site Configuration Views
@method_decorator(login_required, name='dispatch')
class SiteConfigUpdateView(UpdateView):
    model = SiteConfig
    form_class = SiteConfigForm
    template_name = 'cms/site_config_edit.html'
    success_url = reverse_lazy('cms:dashboard')
    
    def get_object(self):
        return SiteConfig.get_site_config()
    
    def form_valid(self, form):
        messages.success(self.request, 'Site configuration updated successfully!')
        return super().form_valid(form)


# Hero Section Views
@method_decorator(login_required, name='dispatch')
class HeroSectionUpdateView(UpdateView):
    """
    View for editing hero section content
    """
    model = SiteConfig
    form_class = HeroSectionForm
    template_name = 'cms/hero_section_edit.html'
    success_url = reverse_lazy('cms:dashboard')
    
    def get_object(self):
        return SiteConfig.get_site_config()
    
    def form_valid(self, form):
        # Handle image clearing
        if self.request.POST.get('hero_background_image-clear'):
            form.instance.hero_background_image.delete(save=False)
            form.instance.hero_background_image = None
        
        messages.success(self.request, 'Hero section updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Hero Section'
        context['page_description'] = 'Update the hero section messaging, CTAs, and social proof elements'
        return context


# VMGO Section Views
@method_decorator(login_required, name='dispatch')
class VMGOSectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for editing VMGO section content
    """
    model = NORSUVMGOHistory
    form_class = VMGOSectionForm
    template_name = 'cms/vmgo_section_edit.html'
    success_url = reverse_lazy('cms:dashboard')

    def test_func(self):
        """Only superusers can edit VMGO section"""
        return self.request.user.is_superuser

    def get_object(self, queryset=None):
        """Get the singleton VMGO section instance"""
        return NORSUVMGOHistory.get_vmgo_section()

    def form_valid(self, form):
        messages.success(self.request, 'VMGO section updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit VMGO Section'
        context['page_description'] = 'Manage NORSU\'s Vision, Mission, Goals, Objectives, and Core Values content'
        return context




# Staff Member Views
@method_decorator(login_required, name='dispatch')
class StaffMemberListView(ListView):
    model = StaffMember
    template_name = 'cms/staff_member_list.html'
    context_object_name = 'staff_members'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class StaffMemberCreateView(CreateView):
    model = StaffMember
    form_class = StaffMemberForm
    template_name = 'cms/staff_member_edit.html'
    success_url = reverse_lazy('cms:staff_member_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Staff member created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class StaffMemberUpdateView(UpdateView):
    model = StaffMember
    form_class = StaffMemberForm
    template_name = 'cms/staff_member_edit.html'
    success_url = reverse_lazy('cms:staff_member_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Staff member updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class StaffMemberDeleteView(DeleteView):
    model = StaffMember
    template_name = 'cms/staff_member_confirm_delete.html'
    success_url = reverse_lazy('cms:staff_member_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Staff member deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Timeline Item Views
@method_decorator(login_required, name='dispatch')
class TimelineItemListView(ListView):
    model = TimelineItem
    template_name = 'cms/timeline_item_list.html'
    context_object_name = 'timeline_items'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class TimelineItemCreateView(CreateView):
    model = TimelineItem
    form_class = TimelineItemForm
    template_name = 'cms/timeline_item_edit.html'
    success_url = reverse_lazy('cms:timeline_item_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Timeline item created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TimelineItemUpdateView(UpdateView):
    model = TimelineItem
    form_class = TimelineItemForm
    template_name = 'cms/timeline_item_edit.html'
    success_url = reverse_lazy('cms:timeline_item_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Timeline item updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TimelineItemDeleteView(DeleteView):
    model = TimelineItem
    template_name = 'cms/timeline_item_confirm_delete.html'
    success_url = reverse_lazy('cms:timeline_item_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Timeline item deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Contact Info Views
@method_decorator(login_required, name='dispatch')
class ContactInfoListView(ListView):
    model = ContactInfo
    template_name = 'cms/contact_info_list.html'
    context_object_name = 'contact_info'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class ContactInfoCreateView(CreateView):
    model = ContactInfo
    form_class = ContactInfoForm
    template_name = 'cms/contact_info_edit.html'
    success_url = reverse_lazy('cms:contact_info_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Contact information created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ContactInfoUpdateView(UpdateView):
    model = ContactInfo
    form_class = ContactInfoForm
    template_name = 'cms/contact_info_edit.html'
    success_url = reverse_lazy('cms:contact_info_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Contact information updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ContactInfoDeleteView(DeleteView):
    model = ContactInfo
    template_name = 'cms/contact_info_confirm_delete.html'
    success_url = reverse_lazy('cms:contact_info_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Contact information deleted successfully!')
        return super().delete(request, *args, **kwargs)


# FAQ Views
@method_decorator(login_required, name='dispatch')
class FAQListView(ListView):
    model = FAQ
    template_name = 'cms/faq_list.html'
    context_object_name = 'faqs'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class FAQCreateView(CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'cms/faq_edit.html'
    success_url = reverse_lazy('cms:faq_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'FAQ created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class FAQUpdateView(UpdateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'cms/faq_edit.html'
    success_url = reverse_lazy('cms:faq_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'FAQ updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class FAQDeleteView(DeleteView):
    model = FAQ
    template_name = 'cms/faq_confirm_delete.html'
    success_url = reverse_lazy('cms:faq_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'FAQ deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Feature Views
@method_decorator(login_required, name='dispatch')
class FeatureListView(ListView):
    model = Feature
    template_name = 'cms/feature_list.html'
    context_object_name = 'features'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class FeatureCreateView(CreateView):
    model = Feature
    form_class = FeatureForm
    template_name = 'cms/feature_edit.html'
    success_url = reverse_lazy('cms:feature_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Feature created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class FeatureUpdateView(UpdateView):
    model = Feature
    form_class = FeatureForm
    template_name = 'cms/feature_edit.html'
    success_url = reverse_lazy('cms:feature_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Feature updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class FeatureDeleteView(DeleteView):
    model = Feature
    template_name = 'cms/feature_confirm_delete.html'
    success_url = reverse_lazy('cms:feature_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Feature deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Testimonial Views
@method_decorator(login_required, name='dispatch')
class TestimonialListView(ListView):
    model = Testimonial
    template_name = 'cms/testimonial_list.html'
    context_object_name = 'testimonials'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class TestimonialCreateView(CreateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'cms/testimonial_edit.html'
    success_url = reverse_lazy('cms:testimonial_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Testimonial created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TestimonialUpdateView(UpdateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'cms/testimonial_edit.html'
    success_url = reverse_lazy('cms:testimonial_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Testimonial updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TestimonialDeleteView(DeleteView):
    model = Testimonial
    template_name = 'cms/testimonial_confirm_delete.html'
    success_url = reverse_lazy('cms:testimonial_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Testimonial deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Alumni Statistics Views
@method_decorator(login_required, name='dispatch')
class AlumniStatisticListView(ListView):
    model = AlumniStatistic
    template_name = 'cms/alumni_statistic_list.html'
    context_object_name = 'statistics'
    paginate_by = 10


@method_decorator(login_required, name='dispatch')
class AlumniStatisticCreateView(CreateView):
    model = AlumniStatistic
    form_class = AlumniStatisticForm
    template_name = 'cms/alumni_statistic_edit.html'
    success_url = reverse_lazy('cms:alumni_statistic_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Alumni statistic created successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class AlumniStatisticUpdateView(UpdateView):
    model = AlumniStatistic
    form_class = AlumniStatisticForm
    template_name = 'cms/alumni_statistic_edit.html'
    success_url = reverse_lazy('cms:alumni_statistic_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Alumni statistic updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class AlumniStatisticDeleteView(DeleteView):
    model = AlumniStatistic
    template_name = 'cms/alumni_statistic_confirm_delete.html'
    success_url = reverse_lazy('cms:alumni_statistic_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Alumni statistic deleted successfully!')
        return super().delete(request, *args, **kwargs)

