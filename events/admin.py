from django.contrib import admin
from django.utils.html import format_html
from .models import Event, EventRSVP


class EventRSVPInline(admin.TabularInline):
    """Inline admin to show RSVPs within Event admin"""
    model = EventRSVP
    extra = 0
    readonly_fields = ('user', 'status', 'notes', 'created_at', 'updated_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        # Prevent adding RSVPs from admin - users should RSVP through the site
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'location', 'is_virtual', 'status', 'rsvp_summary', 'created_by')
    list_filter = ('status', 'is_virtual', 'start_date', 'visibility')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    filter_horizontal = ('notified_groups',)
    readonly_fields = ('created_at', 'updated_at', 'rsvp_summary_detailed')
    inlines = [EventRSVPInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image')
        }),
        ('Event Details', {
            'fields': ('start_date', 'end_date', 'location', 'is_virtual', 'virtual_link', 'max_participants')
        }),
        ('Status and Visibility', {
            'fields': ('status', 'visibility', 'notified_groups')
        }),
        ('RSVP Summary', {
            'fields': ('rsvp_summary_detailed',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def rsvp_summary(self, obj):
        """Show RSVP counts in list view"""
        attending = obj.rsvps.filter(status='yes').count()
        not_attending = obj.rsvps.filter(status='no').count()
        total = attending + not_attending
        
        return format_html(
            '<span style="color: green;">✓ {}</span> | '
            '<span style="color: red;">✗ {}</span> | '
            '<strong>Total: {}</strong>',
            attending, not_attending, total
        )
    rsvp_summary.short_description = 'RSVPs'
    
    def rsvp_summary_detailed(self, obj):
        """Show detailed RSVP information in detail view"""
        attending = obj.rsvps.filter(status='yes').count()
        not_attending = obj.rsvps.filter(status='no').count()
        total = attending + not_attending
        
        if total == 0:
            return format_html('<p style="color: gray;">No RSVPs yet</p>')
        
        attending_percent = (attending / total * 100) if total > 0 else 0
        not_attending_percent = (not_attending / total * 100) if total > 0 else 0
        
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<h3 style="margin-top: 0;">RSVP Statistics</h3>'
            '<p><strong>Total Responses:</strong> {}</p>'
            '<p><span style="color: green; font-weight: bold;">✓ Attending:</span> {} ({:.1f}%)</p>'
            '<p><span style="color: red; font-weight: bold;">✗ Not Attending:</span> {} ({:.1f}%)</p>'
            '</div>',
            total, attending, attending_percent, not_attending, not_attending_percent
        )
    rsvp_summary_detailed.short_description = 'RSVP Statistics'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'user_email', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'event')
    search_fields = ('event__title', 'user__username', 'user__email', 'user__first_name', 'user__last_name', 'notes')
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
    
    def user_email(self, obj):
        """Show user email in list view"""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email' 