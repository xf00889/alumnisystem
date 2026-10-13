from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import messaging_views
from . import circle_views

app_name = 'mentorship'

router = DefaultRouter()
router.register(r'mentors', views.MentorViewSet, basename='mentor')
router.register(r'requests', views.MentorshipRequestViewSet, basename='request')
router.register(r'meetings', views.MentorshipMeetingViewSet, basename='meeting')
router.register(r'messages', views.MentorshipMessageViewSet, basename='message')
router.register(r'progress', views.MentorshipProgressViewSet, basename='progress')
router.register(r'milestones', views.TimelineMilestoneViewSet, basename='milestone')

urlpatterns = [
    path('circle/<int:mentor_id>/', circle_views.mentor_circle, name='mentor_circle'),
    path('circle/<int:mentor_id>/activity/', circle_views.circle_activity, name='circle_activity'),
    path('circle/<int:mentor_id>/send/', circle_views.circle_send, name='circle_send'),
    path('circle/<int:mentor_id>/schedule/', circle_views.circle_schedule, name='circle_schedule'),
    path('circle/<int:mentor_id>/meeting/<int:meeting_id>/cancel/', circle_views.circle_cancel_meeting, name='circle_cancel_meeting'),
    path('circle/<int:mentor_id>/mentee/<int:mentorship_id>/progress/', circle_views.circle_update_progress, name='circle_update_progress'),
    path('circle/<int:mentor_id>/mentee/<int:mentorship_id>/timeline/', circle_views.circle_update_timeline, name='circle_update_timeline'),
    path('', views.mentor_search, name='mentor_search'),
    path('dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('mentee-dashboard/', views.mentee_dashboard, name='mentee_dashboard'),
    path('requests/', views.requests_list, name='requests_list'),
    path('request/<int:mentor_id>/', views.request_mentorship, name='request_mentorship'),
    path('request/<int:request_id>/update-status/', views.update_request_status, name='update_request_status'),
    path('api/', include((router.urls, 'mentorship'), namespace='api')),
    path('mentor/<int:pk>/toggle-availability/', views.MentorViewSet.as_view({'post': 'toggle_availability'}), name='toggle_availability'),
    path('schedule-meeting/', views.MentorshipMeetingViewSet.as_view({'post': 'create'}), name='schedule_meeting'),
    path('send-message/', views.send_message_dashboard, name='send_message'),
    path('api/update-quick-progress/<int:mentorship_id>/', views.update_quick_progress, name='update_quick_progress'),
    path('api/update-mentorship-status/<int:mentorship_id>/', views.update_mentorship_status, name='update_mentorship_status'),
    path('set-timeline/', views.set_timeline, name='set_timeline'),
    path('personal-meeting/<int:meeting_id>/cancel/', circle_views.cancel_personal_meeting, name='cancel_personal_meeting'),
    
    # Messaging URLs
    path('messages/', messaging_views.messaging_page, name='messaging_page'),
    path('messages/sidebar/', messaging_views.conversation_list_view, name='conversation_list'),
    path('messages/conversation/<int:conversation_id>/', messaging_views.conversation_detail_view, name='conversation_detail'),
    path('messages/conversation/<int:conversation_id>/send/', messaging_views.send_message, name='send_message_new'),
    path('messages/create/<int:mentorship_id>/', messaging_views.create_conversation, name='create_conversation'),
    path('messages/create-direct/', messaging_views.create_direct_message, name='create_direct_message'),
]