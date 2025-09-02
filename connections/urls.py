from django.urls import path
from . import views

app_name = 'connections'

urlpatterns = [
    # Connection management URLs
    path('send-request/<int:user_id>/', views.send_connection_request, name='send_request'),
    path('requests/', views.connection_requests, name='connection_requests'),
    path('accept/<int:connection_id>/', views.accept_connection_request, name='accept_request'),
    path('reject/<int:connection_id>/', views.reject_connection_request, name='reject_request'),
    path('my-connections/', views.my_connections, name='my_connections'),
    path('remove/<int:user_id>/', views.remove_connection, name='remove_connection'),
    path('pending-count/', views.pending_requests_count, name='pending_requests_count'),
    path('status/<int:user_id>/', views.connection_status, name='connection_status'),
    
    # Direct messaging URLs
    path('messages/', views.direct_messages, name='conversations_list'),
    path('messages/<int:user_id>/', views.direct_messages, name='direct_messages'),
    path('send-message/<int:user_id>/', views.send_message, name='send_message'),

    # Generic conversation detail URL (redirects to appropriate URL based on conversation type)
    path('conversations/<int:conversation_id>/', views.conversation_detail_redirect, name='conversation_detail'),

    # Group chat URLs
    path('api/create-group/', views.create_group_chat, name='create_group_chat'),
    path('group/<int:conversation_id>/', views.group_chat_detail, name='group_chat_detail'),
    path('group/<int:conversation_id>/send/', views.send_group_message, name='send_group_message'),
    path('group/<int:conversation_id>/upload-photo/', views.upload_group_photo, name='upload_group_photo'),
    path('group/<int:conversation_id>/remove-photo/', views.remove_group_photo, name='remove_group_photo'),
    path('group/<int:conversation_id>/participants/', views.group_participants, name='group_participants'),
    path('group/<int:conversation_id>/remove-participant/', views.remove_group_participant, name='remove_group_participant'),
    path('group/<int:conversation_id>/search-members/', views.search_group_members, name='search_group_members'),
    path('group/<int:conversation_id>/add-members/', views.add_group_members, name='add_group_members'),

    # Test pages
    path('test-search/', views.test_search, name='test_search'),
    path('test-search-api/', views.test_search_api, name='test_search_api'),
    path('test-inline/', views.test_inline_interface, name='test_inline_interface'),
]