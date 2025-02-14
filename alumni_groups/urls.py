from django.urls import path
from . import views

app_name = 'alumni_groups'

urlpatterns = [
    # Group List and Creation
    path('', views.GroupListView.as_view(), name='group_list'),
    path('create/', views.GroupCreateView.as_view(), name='group_create'),
    path('map/', views.group_map_view, name='group_map'),
    
    # Group Detail and Management
    path('<slug:slug>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('<slug:slug>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('<slug:slug>/join/', views.join_group, name='group_join'),
    path('<slug:slug>/join-with-questions/', views.join_group_with_questions, name='join_group_with_questions'),
    path('<slug:slug>/leave/', views.leave_group, name='group_leave'),
    path('<slug:slug>/manage-members/', views.manage_members, name='manage_members'),
    
    # Security Questions Management
    path('<slug:slug>/security-questions/', views.manage_security_questions, name='manage_security_questions'),
    path('<slug:slug>/review-answers/<int:membership_id>/', views.review_membership_answers, name='review_membership_answers'),
    
    # API Endpoints
    path('api/nearby/', views.nearby_groups_api, name='nearby_groups_api'),
    path('api/<slug:slug>/analytics/', views.group_analytics_api, name='group_analytics_api'),
    path('api/<slug:slug>/messages/send/', views.send_message, name='send_message'),
    path('api/<slug:slug>/messages/get/', views.get_messages, name='get_messages'),
    path('api/member/<int:membership_id>/status/', views.update_member_status, name='update_member_status'),
    path('api/member/<int:membership_id>/security-answers/', views.get_security_answers, name='get_security_answers'),
] 