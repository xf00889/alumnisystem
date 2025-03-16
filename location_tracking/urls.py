from django.urls import path
from . import views

app_name = 'location_tracking'

urlpatterns = [
    path('map/', views.map_view, name='map'),
    path('update-location/', views.update_location, name='update_location'),
    path('get-locations/', views.get_all_locations, name='get_locations'),
] 