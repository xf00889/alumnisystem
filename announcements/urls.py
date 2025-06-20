from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.AnnouncementListView.as_view(), name='announcement-list'),
    path('<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('new/', views.AnnouncementCreateView.as_view(), name='announcement-create'),
    path('<int:pk>/update/', views.AnnouncementUpdateView.as_view(), name='announcement-update'),
    path('<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement-delete'),
    path('search/', views.announcement_search, name='announcement-search'),
    path('public/', views.PublicAnnouncementListView.as_view(), name='public-announcement-list'),
    path('public/<int:pk>/', views.PublicAnnouncementDetailView.as_view(), name='public-announcement-detail'),
    path('public/new/', views.PublicAnnouncementCreateView.as_view(), name='create-public-announcement'),
] 