from django.urls import path
from . import views
from .directory_employability import directory_employability_export

app_name = 'alumni_directory'

urlpatterns = [
    path('', views.alumni_list, name='alumni_list'),
    path('tabular/', views.tabular_alumni_list, name='tabular_alumni_list'),
    path('management/', views.alumni_management, name='alumni_management'),
    path('employability/export/', directory_employability_export, name='employability_export'),
    path('<int:pk>/', views.alumni_detail, name='alumni_detail'),
    path('alumni/<int:pk>/detail-modal/', views.alumni_detail_modal, name='alumni_detail_modal'),
    path('document/<int:doc_id>/download/', views.download_document, name='download_document'),
    path('<int:pk>/send-reminder/', views.send_reminder, name='send_reminder'),
]