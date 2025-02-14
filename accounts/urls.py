from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('edit/', views.edit_personal_info, name='edit_profile'),
    path('update/', views.profile_update, name='profile_update'),
    path('update/personal-info/', views.update_personal_info, name='update_personal_info'),
    path('update/skills/', views.update_skills, name='update_skills'),
    path('update/education/', views.update_education, name='update_education'),
    path('update/education/<int:pk>/', views.edit_education, name='edit_education'),
    path('update/education/<int:pk>/delete/', views.delete_education, name='delete_education'),
    path('update/experience/', views.update_experience, name='update_experience'),
    path('update/documents/', views.update_documents, name='update_documents'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('post-registration/', views.post_registration, name='post_registration'),
    # API endpoints
    path('api/search-users/', views.search_users_api, name='search_users_api'),
    path('api/user/<int:user_id>/', views.user_detail_api, name='user_detail_api'),
    path('group/<int:group_id>/manage-members/', views.manage_members, name='manage_members'),
    path('member/<int:membership_id>/update-status/', views.update_member_status, name='update_member_status'),
    path('member/<int:membership_id>/security-answer/', views.view_security_answer, name='view_security_answer'),
] 