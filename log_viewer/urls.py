from django.urls import path
from . import views

app_name = 'log_viewer'

urlpatterns = [
    path('', views.logs, name='logs'),  # Main logs page with tabs
    path('file/', views.log_list, name='log_list'),  # Legacy file logs
    path('detail/<int:log_id>/', views.log_detail, name='log_detail'),
    path('export/', views.log_export, name='log_export'),
    path('clear/', views.log_clear, name='log_clear'),
    # Audit log views
    path('audit/', views.audit_log_list, name='audit_log_list'),
    path('audit/<int:log_id>/', views.audit_log_detail, name='audit_log_detail'),
    path('audit/export/', views.audit_log_export, name='audit_log_export'),
]

