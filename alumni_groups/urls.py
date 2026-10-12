from django.urls import path
from . import views, community_views

app_name = 'alumni_groups'

urlpatterns = [
    # Group List and Creation
    path('', views.GroupListView.as_view(), name='group_list'),
    path('create/', views.GroupCreateView.as_view(), name='group_create'),
    path('create-progressive/', views.GroupCreateProgressiveView.as_view(), name='group_create_progressive'),
    path('create-phase1/', views.GroupCreatePhase1View.as_view(), name='group_create_phase1'),
    path('create-phase2/', views.GroupCreatePhase2View.as_view(), name='group_create_phase2'),
    path('map/', views.group_map_view, name='group_map'),
    
    # Group Detail and Management
    path('<slug:slug>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('<slug:slug>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('<slug:slug>/join/', views.join_group, name='join_group'),
    path('<slug:slug>/join-with-questions/', views.join_group_with_questions, name='join_group_with_questions'),
    path('<slug:slug>/leave/', views.leave_group, name='group_leave'),
    path('<slug:slug>/leave/confirm/', views.get_leave_group, name='get_leave_group'),
    path('<slug:slug>/manage-members/', views.manage_members, name='manage_members'),
    
    # Security Questions Management
    path('<slug:slug>/security-questions/', views.manage_security_questions, name='manage_security_questions'),
    path('<slug:slug>/settings/update/', views.update_group_settings, name='update_group_settings'),
    path('<slug:slug>/review-answers/<int:membership_id>/', views.review_membership_answers, name='review_membership_answers'),
    
    # API Endpoints
    path('api/nearby/', views.nearby_groups_api, name='nearby_groups_api'),
    path('api/<slug:slug>/analytics/', views.group_analytics_api, name='group_analytics_api'),
    path('api/<slug:slug>/messages/send/', views.send_message, name='send_message'),
    path('api/<slug:slug>/messages/get/', views.get_messages, name='get_messages'),
    path('api/member/<int:membership_id>/status/', views.update_member_status, name='update_member_status'),
    path('api/member/<int:membership_id>/security-answers/', views.get_security_answers, name='get_security_answers'),

    # Community actions (all mutations are POST-only, CSRF protected).
    path('post/<int:post_id>/bookmark/', community_views.toggle_bookmark, name='toggle_bookmark'),
    path('post/<int:post_id>/report/', community_views.report_post, name='report_post'),
    path('post/<int:post_id>/pin/', community_views.pin_post, name='pin_post'),
    path('reports/<int:report_id>/review/', community_views.review_report, name='review_report'),
    path('<slug:slug>/polls/create/', community_views.create_poll, name='create_poll'),
    path('polls/<int:poll_id>/vote/', community_views.vote_poll, name='vote_poll'),
    path('<slug:slug>/events/create/', community_views.create_group_event, name='create_group_event'),
    path('events/<int:event_id>/rsvp/', community_views.rsvp_event, name='rsvp_event'),
    path('<slug:slug>/discussions/create/', community_views.create_discussion, name='create_discussion'),
    path('discussions/<int:discussion_id>/reply/', community_views.reply_discussion, name='reply_discussion'),
    path('discussions/<int:discussion_id>/moderate/', community_views.moderate_discussion, name='moderate_discussion'),
    path('notifications/<int:notification_id>/read/', community_views.mark_notification_read, name='mark_notification_read'),
    path('event-shares/<int:share_id>/review/', community_views.handle_event_share, name='handle_event_share'),

    # Feed URLs
    path('<slug:slug>/feed/refresh/', views.group_feed_snapshot, name='feed_snapshot'),
    path('group/<slug:slug>/post/create/', views.create_post, name='create_post'),
    path('api/post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('api/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('api/post/<int:post_id>/comments/', views.get_post_comments, name='get_post_comments'),
    path('api/post/<int:post_id>/approve/', views.approve_post, name='approve_post'),
] 