from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('my-feedbacks/', views.my_feedbacks, name='my_feedbacks'),
    path('manage/', views.manage_feedbacks, name='manage_feedbacks'),
    path('update/<int:pk>/', views.update_feedback, name='update_feedback'),
] 