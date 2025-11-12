from django.urls import path
from . import views

app_name = 'log_viewer'

urlpatterns = [
    path('', views.logs, name='logs'),  # Main logs page with tabs
    path('file/', views.log_list, name='log_list'),  # Legacy file logs
    path('detail/<int:log_id>/', views.log_detail, name='log_detail'),
    path('export/', views.log_export, name='log_export'),
    # Audit log views
    path('audit/', views.audit_log_list, name='audit_log_list'),
    path('audit/<int:log_id>/', views.audit_log_detail, name='audit_log_detail'),
    path('audit/export/', views.audit_log_export, name='audit_log_export'),
    # Log management dashboard (legacy)
    path('management/', views.log_management_dashboard, name='log_management_dashboard'),
    path('management/trigger/', views.manual_cleanup_trigger, name='manual_cleanup_trigger'),
    # Unified dashboard
    path('unified/', views.unified_dashboard, name='unified_dashboard'),
    # API endpoints for unified dashboard
    path('api/save-retention-policy/', views.save_retention_policy, name='save_retention_policy'),
    path('api/save-cleanup-schedule/', views.save_cleanup_schedule, name='save_cleanup_schedule'),
    path('api/save-storage-config/', views.save_storage_config, name='save_storage_config'),
    path('api/recalculate-storage/', views.recalculate_storage, name='recalculate_storage'),
    path('api/filter-operations/', views.filter_operations, name='filter_operations'),
    path('api/operation/<int:operation_id>/', views.operation_detail, name='operation_detail'),
    path('api/export-operations/', views.export_operations, name='export_operations'),
]

