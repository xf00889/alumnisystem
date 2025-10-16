from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('careers/', views.careers, name='careers'),
    path('job/<int:job_id>/details/', views.get_job_details, name='get_job_details'),
    path('job/<int:job_id>/check-eligibility/', views.check_job_application_eligibility, name='check_job_application_eligibility'),
    path('manage/', views.manage_jobs, name='manage_jobs'),
    path('post/', views.post_job, name='post_job'),
    path('bulk-update/', views.bulk_update_jobs, name='bulk_update_jobs'),

    path('application/<int:application_id>/details/', views.application_details, name='application_details'),
    path('application/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('application/<int:application_id>/send-email/', views.send_application_email, name='send_application_email'),
    path('export/<int:job_id>/applicants/', views.export_applicants, name='export_applicants'),
    
    # Job Scraper URLs (must be before slug patterns)
    path('scraper/', views.job_scraper, name='job_scraper'),
    path('scraper/results/', views.job_scraper_results, name='job_scraper_results'),
    path('scraper/redirect/<str:job_id>/', views.job_redirect, name='job_redirect'),
    
    # Slug-based patterns (must be last)
    path('<slug:slug>/', views.job_detail, name='job_detail'),
    path('<slug:slug>/edit/', views.edit_job, name='edit_job'),
    path('<slug:slug>/delete/', views.delete_job, name='delete_job'),
    path('<slug:slug>/apply/', views.apply_for_job, name='apply_for_job'),
    path('<slug:slug>/applications/', views.manage_applications, name='manage_applications')
]

