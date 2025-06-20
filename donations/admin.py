from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CampaignType, Campaign, Donation, DonorRecognition, CampaignUpdate

@admin.register(CampaignType)
class CampaignTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign_type', 'goal_amount', 'current_amount', 
                    'progress_percentage', 'start_date', 'end_date', 'status', 'is_featured')
    list_filter = ('status', 'campaign_type', 'is_featured', 'start_date')
    search_fields = ('name', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'short_description', 'description', 'campaign_type', 
                      'featured_image', 'created_by')
        }),
        (_('Financial Information'), {
            'fields': ('goal_amount', 'current_amount')
        }),
        (_('Campaign Timeline'), {
            'fields': ('start_date', 'end_date', 'status')
        }),
        (_('Display Options'), {
            'fields': ('is_featured',)
        }),
        (_('System Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CampaignUpdate)
class CampaignUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'campaign', 'is_featured', 'created', 'created_by')
    list_filter = ('is_featured', 'created', 'campaign')
    search_fields = ('title', 'content', 'campaign__name')
    readonly_fields = ('created', 'updated')
    fieldsets = (
        (_('Update Information'), {
            'fields': ('title', 'campaign', 'content', 'image', 'is_featured', 'created_by')
        }),
        (_('System Information'), {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('get_donor_display', 'campaign', 'amount', 'status', 
                   'payment_method', 'donation_date', 'receipt_sent')
    list_filter = ('status', 'payment_method', 'receipt_sent', 'donation_date', 'campaign')
    search_fields = ('donor__first_name', 'donor__last_name', 'donor__email', 
                    'donor_name', 'donor_email', 'campaign__name', 'reference_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Donation Information'), {
            'fields': ('campaign', 'amount', 'donation_date', 'status', 'payment_method', 'reference_number')
        }),
        (_('Donor Information'), {
            'fields': ('donor', 'is_anonymous', 'donor_name', 'donor_email')
        }),
        (_('Additional Information'), {
            'fields': ('message', 'receipt_sent')
        }),
        (_('System Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_donor_display(self, obj):
        if obj.is_anonymous:
            return _("Anonymous")
        elif obj.donor:
            return obj.donor.get_full_name()
        else:
            return obj.donor_name
    get_donor_display.short_description = _("Donor")

@admin.register(DonorRecognition)
class DonorRecognitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'minimum_amount', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fieldsets = (
        (_('Recognition Level'), {
            'fields': ('name', 'description', 'minimum_amount', 'badge_image', 'is_active')
        }),
    )
