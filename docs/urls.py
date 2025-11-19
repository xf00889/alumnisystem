"""
URL configuration for documentation viewer app.
"""
from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    # Documentation index (main landing page)
    path('', views.DocumentationIndexView.as_view(), name='index'),
    
    # Search functionality
    path('search/', views.DocumentationSearchView.as_view(), name='search'),
    
    # Individual document view (must be last to catch all paths)
    path('<path:doc_path>/', views.DocumentationView.as_view(), name='document'),
]
