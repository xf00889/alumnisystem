from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    # Campaign views
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/create/', views.campaign_create, name='campaign_create'),
    path('campaigns/<slug:slug>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<slug:slug>/donors/', views.campaign_donors, name='campaign_donors'),
    path('campaigns/<int:pk>/edit/', views.campaign_edit, name='campaign_edit'),
    
    # Donation views
    path('history/', views.donation_history, name='donation_history'),
    path('confirmation/<int:pk>/', views.donation_confirmation, name='donation_confirmation'),
    
    # Admin views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage/donations/', views.manage_donations, name='manage_donations'),
    path('manage/campaigns/', views.manage_campaigns, name='manage_campaigns'),
    path('donation/<int:pk>/update-status/', views.update_donation_status, name='update_donation_status'),
    path('donation/<int:pk>/delete/', views.delete_donation, name='delete_donation'),
    path('donation/<int:pk>/edit-form/', views.donation_edit_form, name='donation_edit_form'),
    path('donation/<int:pk>/edit/', views.edit_donation, name='edit_donation'),
    path('donation/<int:pk>/send-receipt/', views.send_donation_receipt, name='send_donation_receipt'),
    path('campaign/<int:pk>/update-status/', views.update_campaign_status, name='update_campaign_status'),
    path('campaign/<int:pk>/delete/', views.delete_campaign, name='delete_campaign'),
] 