from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'category', 'user', 'status', 'priority', 'created_at')
    list_filter = ('status', 'category', 'priority', 'created_at')
    search_fields = ('subject', 'message', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'category', 'subject', 'message', 'attachment')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Admin', {
            'fields': ('admin_notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(status__in=['pending', 'in_progress'])
