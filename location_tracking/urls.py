from django.urls import path
from . import views

app_name = 'location_tracking'
urlpatterns = [
    path('map/', views.map_view, name='map'),
    path('update-location/', views.update_location, name='update_location'),
    path('sharing-status/', views.sharing_status, name='sharing_status'),
    path('get-locations/', views.get_all_locations, name='get_locations'),
    path('stop-sharing/', views.stop_sharing_location, name='stop_sharing'),
    path('address/<int:position_id>/', views.lookup_street_address, name='lookup_address'),
]
