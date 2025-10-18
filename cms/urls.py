from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.CMSDashboardView.as_view(), name='dashboard'),
    
    # Site Configuration
    path('site-config/', views.SiteConfigUpdateView.as_view(), name='site_config_edit'),
    
    # Page Sections
    path('page-sections/', views.PageSectionListView.as_view(), name='page_section_list'),
    path('page-sections/create/', views.PageSectionCreateView.as_view(), name='page_section_create'),
    path('page-sections/<int:pk>/edit/', views.PageSectionUpdateView.as_view(), name='page_section_edit'),
    path('page-sections/<int:pk>/delete/', views.PageSectionDeleteView.as_view(), name='page_section_delete'),
    
    # Static Pages
    path('static-pages/', views.StaticPageListView.as_view(), name='static_page_list'),
    path('static-pages/create/', views.StaticPageCreateView.as_view(), name='static_page_create'),
    path('static-pages/<int:pk>/edit/', views.StaticPageUpdateView.as_view(), name='static_page_edit'),
    
    # Staff Members
    path('staff-members/', views.StaffMemberListView.as_view(), name='staff_member_list'),
    path('staff-members/create/', views.StaffMemberCreateView.as_view(), name='staff_member_create'),
    path('staff-members/<int:pk>/edit/', views.StaffMemberUpdateView.as_view(), name='staff_member_edit'),
    
    # Timeline Items
    path('timeline-items/', views.TimelineItemListView.as_view(), name='timeline_item_list'),
    path('timeline-items/create/', views.TimelineItemCreateView.as_view(), name='timeline_item_create'),
    path('timeline-items/<int:pk>/edit/', views.TimelineItemUpdateView.as_view(), name='timeline_item_edit'),
    
    # Contact Information
    path('contact-info/', views.ContactInfoListView.as_view(), name='contact_info_list'),
    path('contact-info/create/', views.ContactInfoCreateView.as_view(), name='contact_info_create'),
    path('contact-info/<int:pk>/edit/', views.ContactInfoUpdateView.as_view(), name='contact_info_edit'),
    
    # FAQs
    path('faqs/', views.FAQListView.as_view(), name='faq_list'),
    path('faqs/create/', views.FAQCreateView.as_view(), name='faq_create'),
    path('faqs/<int:pk>/edit/', views.FAQUpdateView.as_view(), name='faq_edit'),
    
    # Features
    path('features/', views.FeatureListView.as_view(), name='feature_list'),
    path('features/create/', views.FeatureCreateView.as_view(), name='feature_create'),
    path('features/<int:pk>/edit/', views.FeatureUpdateView.as_view(), name='feature_edit'),
    
    # Testimonials
    path('testimonials/', views.TestimonialListView.as_view(), name='testimonial_list'),
    path('testimonials/create/', views.TestimonialCreateView.as_view(), name='testimonial_create'),
    path('testimonials/<int:pk>/edit/', views.TestimonialUpdateView.as_view(), name='testimonial_edit'),
]
