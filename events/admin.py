from django.contrib import admin
from .models import Event, EventRSVP

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'location', 'is_virtual', 'status', 'created_by')
    list_filter = ('status', 'is_virtual', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    filter_horizontal = ('notified_groups',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image')
        }),
        ('Event Details', {
            'fields': ('start_date', 'end_date', 'location', 'is_virtual', 'virtual_link', 'max_participants')
        }),
        ('Status and Groups', {
            'fields': ('status', 'notified_groups')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'event')
    search_fields = ('event__title', 'user__username', 'user__email', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('event', 'user', 'status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ) 