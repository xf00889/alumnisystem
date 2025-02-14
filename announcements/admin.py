from django.contrib import admin
from django.contrib import messages
from .models import Announcement, Category
from .utils import send_announcement_notification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority_level', 'target_audience', 'date_posted', 'is_active', 'views_count')
    list_filter = ('category', 'priority_level', 'target_audience', 'is_active', 'date_posted')
    search_fields = ('title', 'content')
    date_hierarchy = 'date_posted'
    ordering = ('-date_posted',)
    readonly_fields = ('views_count',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        ('Classification', {
            'fields': ('category', 'priority_level', 'target_audience')
        }),
        ('Status', {
            'fields': ('is_active', 'views_count')
        }),
        ('Dates', {
            'fields': ('date_posted',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save_model to send email notifications when announcement is created"""
        is_new = not obj.pk  # Check if this is a new announcement
        super().save_model(request, obj, form, change)
        
        # Send email notification only for new announcements that are active
        if is_new and obj.is_active:
            if send_announcement_notification(obj):
                self.message_user(request, "Announcement was created and email notifications were sent successfully.", messages.SUCCESS)
            else:
                self.message_user(request, "Announcement was created but there was an error sending email notifications.", messages.WARNING)
