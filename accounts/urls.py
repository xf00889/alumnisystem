from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import security_views

app_name = 'accounts'
urlpatterns = [
    path('profile/', views.profile_detail, name='profile_detail'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('post-registration/', views.post_registration, name='post_registration'),
    path('api/search-users/', views.search_users_api, name='search_users_api'),
    path('api/search-connected-users/', views.search_connected_users_api, name='search_connected_users_api'),
    path('update/skills/', views.update_skills, name='update_skills'),
    path('update/education/', views.update_education, name='update_education'),
    path('update/experience/', views.update_experience, name='update_experience'),
    path('admin/mentor-list/', views.admin_mentor_list, name='admin_mentor_list'),
    path('admin/review-mentor-applications/', views.review_mentor_applications, name='review_mentor_applications'),
    path('edit-profile/', views.profile_update, name='edit_profile'),
    path('apply-mentor/', views.apply_mentor, name='apply_mentor'),
    path('update/documents/', views.update_documents, name='update_documents'),
    path('edit/education/<int:pk>/', views.edit_education, name='edit_education'),
    path('delete/education/<int:pk>/', views.delete_education, name='delete_education'),
    path('edit/experience/<int:pk>/', views.edit_experience, name='edit_experience'),
    path('delete/experience/<int:pk>/', views.delete_experience, name='delete_experience'),
    path('edit/personal-info/', views.edit_personal_info, name='edit_personal_info'),
    path('update/personal-info/', views.update_personal_info, name='update_personal_info'),
    path('document/delete/<int:pk>/', views.document_delete, name='document_delete'),
    path('user/<int:user_id>/', views.user_detail_api, name='user_detail_api'),
    path('manage/members/<int:group_id>/', views.manage_members, name='manage_members'),
    path('update/member-status/<int:membership_id>/', views.update_member_status, name='update_member_status'),
    path('view/security-answer/<int:membership_id>/', views.view_security_answer, name='view_security_answer'),
    path('add/career-path/', views.add_career_path, name='add_career_path'),
    path('edit/career-path/<int:pk>/', views.edit_career_path, name='edit_career_path'),
    path('delete/career-path/<int:pk>/', views.delete_career_path, name='delete_career_path'),
    path('add/achievement/', views.add_achievement, name='add_achievement'),
    path('edit/achievement/<int:pk>/', views.edit_achievement, name='edit_achievement'),
    path('delete/achievement/<int:pk>/', views.delete_achievement, name='delete_achievement'),
    path('skill-matching/', views.skill_matching, name='skill_matching'),
    path('mentor-application-status/', views.mentor_application_status, name='mentor_application_status'),
    path('review/mentor-application/<int:application_id>/', views.review_mentor_application, name='review_mentor_application'),
    
    # Security endpoints
    path('security/send-verification-code/', security_views.send_verification_code, name='send_verification_code'),
    path('security/verify-code/', security_views.verify_code, name='verify_code'),
    path('security/password-reset/', security_views.enhanced_password_reset, name='enhanced_password_reset'),
    path('security/change-password/', security_views.change_password, name='change_password'),
    path('security/check-email/', security_views.check_email_availability, name='check_email_availability'),
    path('security/dashboard/', security_views.SecurityDashboardView.as_view(), name='security_dashboard'),
    
    # Enhanced signup endpoint for tabbed login page
    path('enhanced-signup/', security_views.enhanced_signup, name='enhanced_signup'),
    
    # Email verification endpoints
    path('verify-email/', security_views.verify_email, name='verify_email'),
    path('resend-verification-code/', security_views.resend_verification_code, name='resend_verification_code'),
    path('check-resend-countdown/', security_views.check_resend_countdown, name='check_resend_countdown'),
    path('signup-redirect/', security_views.custom_signup_redirect, name='custom_signup_redirect'),
    
    # Enhanced Password Reset Flow
    path('password-reset-email/', security_views.password_reset_email, name='password_reset_email'),
    path('password-reset-otp/', security_views.password_reset_otp, name='password_reset_otp'),
    path('password-reset-new-password/', security_views.password_reset_new_password, name='password_reset_new_password'),
    path('resend-password-reset-otp/', security_views.resend_password_reset_otp, name='resend_password_reset_otp'),
    path('check-password-reset-countdown/', security_views.check_password_reset_countdown, name='check_password_reset_countdown'),
]
