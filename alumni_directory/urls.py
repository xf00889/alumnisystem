from django.urls import path
from . import views

app_name = 'alumni_directory'

urlpatterns = [
    path('', views.alumni_list, name='alumni_list'),
    path('<int:pk>/', views.alumni_detail, name='alumni_detail'),
    path('document/<int:doc_id>/download/', views.download_document, name='download_document'),
    path('<int:pk>/send-reminder/', views.send_reminder, name='send_reminder'),
] 