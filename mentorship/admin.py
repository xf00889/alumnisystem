from django.contrib import admin
from django.utils.html import format_html
from .models import MentorshipMeeting, MentorshipMessage, MentorshipProgress

@admin.register(MentorshipMeeting)
class MentorshipMeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentorship', 'meeting_date', 'status', 'duration')
    list_filter = ('status', 'meeting_date')
    search_fields = ('title', 'description', 'mentorship__mentor__user__username', 'mentorship__mentee__username')
    date_hierarchy = 'meeting_date'
    ordering = ('-meeting_date',)

@admin.register(MentorshipMessage)
class MentorshipMessageAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'mentorship', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'mentorship__mentor__user__username', 'mentorship__mentee__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username

@admin.register(MentorshipProgress)
class MentorshipProgressAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentorship', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description', 'mentorship__mentor__user__username', 'mentorship__mentee__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
