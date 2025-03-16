from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Public views
    path('', views.job_list, name='job_list'),
    
    # Management views
    path('manage/', views.manage_jobs, name='manage_jobs'),
    path('post/', views.post_job, name='post_job'),
    
    # AJAX endpoints
    path('applications/<int:application_id>/update-status/', 
         views.update_application_status, name='update_application_status'),
    path('applications/<int:application_id>/details/', 
         views.application_details, name='application_details'),
    path('applications/<int:application_id>/add-note/', 
         views.add_application_note, name='add_application_note'),
    path('applications/<int:application_id>/send-email/', views.send_application_email, name='send_application_email'),
    
    # Export functionality
    path('export-applicants/<int:job_id>/', views.export_applicants, name='export_applicants'),
    
    # Job detail views (must come after other specific paths)
    path('<slug:slug>/edit/', views.edit_job, name='edit_job'),
    path('<slug:slug>/delete/', views.delete_job, name='delete_job'),
    path('<slug:slug>/applications/', views.manage_applications, name='manage_applications'),
    path('<slug:slug>/apply/', views.apply_for_job, name='apply_for_job'),
    path('<slug:slug>/', views.job_detail, name='job_detail'),
] 