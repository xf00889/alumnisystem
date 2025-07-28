from django.urls import path
from . import views
from .admin import admin_mentor_list

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_detail, name='profile_detail'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    path('edit/', views.edit_personal_info, name='edit_profile'),
    path('update/', views.profile_update, name='profile_update'),
    path('update/personal-info/', views.update_personal_info, name='update_personal_info'),
    path('update/skills/', views.update_skills, name='update_skills'),
    path('update/education/', views.update_education, name='update_education'),
    path('update/education/<int:pk>/', views.edit_education, name='edit_education'),
    path('update/education/<int:pk>/delete/', views.delete_education, name='delete_education'),
    path('update/experience/', views.update_experience, name='update_experience'),
    path('update/experience/<int:pk>/', views.edit_experience, name='edit_experience'),
    path('update/experience/<int:pk>/delete/', views.delete_experience, name='delete_experience'),
    path('update/documents/', views.update_documents, name='update_documents'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('post-registration/', views.post_registration, name='post_registration'),
    # API endpoints
    path('api/search-users/', views.search_users_api, name='search_users_api'),
    path('api/search-connected-users/', views.search_connected_users_api, name='search_connected_users_api'),
    path('api/user/<int:user_id>/', views.user_detail_api, name='user_detail_api'),
    path('group/<int:group_id>/manage-members/', views.manage_members, name='manage_members'),
    path('member/<int:membership_id>/update-status/', views.update_member_status, name='update_member_status'),
    path('member/<int:membership_id>/security-answer/', views.view_security_answer, name='view_security_answer'),
    # Career Path URLs
    path('career-path/add/', views.add_career_path, name='add_career_path'),
    path('career-path/<int:pk>/edit/', views.edit_career_path, name='edit_career_path'),
    path('career-path/<int:pk>/delete/', views.delete_career_path, name='delete_career_path'),
    # Achievement URLs
    path('achievement/add/', views.add_achievement, name='add_achievement'),
    path('achievement/<int:pk>/edit/', views.edit_achievement, name='edit_achievement'),
    path('achievement/<int:pk>/delete/', views.delete_achievement, name='delete_achievement'),
    # Mentor Application
    path('apply-mentor/', views.apply_mentor, name='apply_mentor'),
    path('mentor-application-status/', views.mentor_application_status, name='mentor_application_status'),
    path('review-mentor-applications/', views.review_mentor_applications, name='review_mentor_applications'),
    path('review-mentor-application/<int:application_id>/', views.review_mentor_application, name='review_mentor_application'),
    
    # Admin Views
    path('admin/mentor-list/', views.admin_mentor_list, name='admin_mentor_list'),
]