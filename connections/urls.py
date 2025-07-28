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

    # Test page
    path('test-search/', views.test_search, name='test_search'),
]