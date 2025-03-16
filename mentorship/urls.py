from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'mentorship'

router = DefaultRouter()
router.register(r'mentors', views.MentorViewSet, basename='mentor')
router.register(r'requests', views.MentorshipRequestViewSet, basename='request')
router.register(r'meetings', views.MentorshipMeetingViewSet, basename='meeting')
router.register(r'messages', views.MentorshipMessageViewSet, basename='message')
router.register(r'progress', views.MentorshipProgressViewSet, basename='progress')
router.register(r'milestones', views.TimelineMilestoneViewSet, basename='milestone')

urlpatterns = [
    path('', views.mentor_search, name='mentor_search'),
    path('dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('mentee-dashboard/', views.mentee_dashboard, name='mentee_dashboard'),
    path('request/<int:mentor_id>/', views.request_mentorship, name='request_mentorship'),
    path('api/', include((router.urls, 'mentorship'), namespace='api')),
    path('mentor/<int:pk>/toggle-availability/', views.MentorViewSet.as_view({'post': 'toggle_availability'}), name='toggle_availability'),
    path('request/<int:pk>/update-status/', views.MentorshipRequestViewSet.as_view({'post': 'update_status'}), name='update_request_status'),
    path('schedule-meeting/', views.MentorshipMeetingViewSet.as_view({'post': 'create'}), name='schedule_meeting'),
    path('send-message/', views.MentorshipMessageViewSet.as_view({'post': 'create'}), name='send_message'),
    path('api/update-quick-progress/<int:mentorship_id>/', views.update_quick_progress, name='update_quick_progress'),
    path('api/update-mentorship-status/<int:mentorship_id>/', views.update_mentorship_status, name='update_mentorship_status'),
    path('set-timeline/', views.set_timeline, name='set_timeline'),
] 