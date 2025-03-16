from django.contrib import admin
from .models import LocationData

@admin.register(LocationData)
class LocationDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'timestamp', 'is_active')
    list_filter = ('is_active', 'timestamp')
    search_fields = ('user__username', 'user__email')
    ordering = ('-timestamp',)
