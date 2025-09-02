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

    # GCash payment flow
    path('payment-instructions/<int:pk>/', views.payment_instructions, name='payment_instructions'),
    path('upload-proof/<int:pk>/', views.upload_payment_proof, name='upload_payment_proof'),

    # Status tracking
    path('track/', views.donation_status_tracker, name='donation_status_tracker'),
    path('track/<str:reference_number>/', views.donation_status_tracker, name='donation_status_tracker'),
    path('api/status/<int:pk>/', views.donation_status_api, name='donation_status_api'),

    # Help and FAQ
    path('faq/', views.donation_faq, name='donation_faq'),

    # Admin views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('verification/', views.verification_dashboard, name='verification_dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('fraud-monitoring/', views.fraud_monitoring_dashboard, name='fraud_monitoring_dashboard'),
    path('verify-donation/<int:pk>/', views.verify_donation, name='verify_donation'),
    path('bulk-verify/', views.bulk_verify_donations, name='bulk_verify_donations'),
    path('resolve-fraud-alert/<int:alert_id>/', views.resolve_fraud_alert, name='resolve_fraud_alert'),
    path('export/', views.export_donations, name='export_donations'),
    path('manage/donations/', views.manage_donations, name='manage_donations'),
    # GCash management (custom interface)
    path('manage/gcash/', views.manage_gcash, name='manage_gcash'),

    path('manage/campaigns/', views.manage_campaigns, name='manage_campaigns'),
    path('donation/<int:pk>/update-status/', views.update_donation_status, name='update_donation_status'),
    path('donation/<int:pk>/delete/', views.delete_donation, name='delete_donation'),
    path('donation/<int:pk>/edit-form/', views.donation_edit_form, name='donation_edit_form'),
    path('donation/<int:pk>/edit/', views.edit_donation, name='edit_donation'),
    path('donation/<int:pk>/send-receipt/', views.send_donation_receipt, name='send_donation_receipt'),
    path('campaign/<int:pk>/update-status/', views.update_campaign_status, name='update_campaign_status'),
    path('campaign/<int:pk>/delete/', views.delete_campaign, name='delete_campaign'),
    # GCash management (staff)
    path('manage/gcash/', views.manage_gcash, name='manage_gcash'),

]