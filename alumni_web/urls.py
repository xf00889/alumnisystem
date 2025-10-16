from django.urls import path
from django.http import HttpResponse

def placeholder_view(request):
    """Placeholder view for alumni_web app"""
    return HttpResponse('Alumni Web - Coming Soon')

app_name = 'alumni_web'

urlpatterns = [
    path('', placeholder_view, name='placeholder'),
]