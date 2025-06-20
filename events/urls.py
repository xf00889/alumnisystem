from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('<int:pk>/rsvp/', views.event_rsvp, name='event_rsvp'),
    path('my-events/', views.my_events, name='my_events'),
    
    path('public/', views.PublicEventListView.as_view(), name='public_event_list'),
    path('public/<int:pk>/', views.PublicEventDetailView.as_view(), name='public_event_detail'),
    path('public/new/', views.PublicEventCreateView.as_view(), name='create_public_event'),
] 