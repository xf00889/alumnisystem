from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    CampaignType, Campaign, Donation, DonorRecognition, CampaignUpdate,
    GCashConfig, FraudAlert, BlacklistedEntity
)

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
                   'reference_number', 'donation_date', 'verified_by')
    list_filter = ('status', 'receipt_sent', 'donation_date', 'campaign', 'verified_by')
    search_fields = ('donor__first_name', 'donor__last_name', 'donor__email',
                    'donor_name', 'donor_email', 'campaign__name', 'reference_number', 'gcash_transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'reference_number')
    fieldsets = (
        (_('Donation Information'), {
            'fields': ('campaign', 'amount', 'donation_date', 'status', 'reference_number')
        }),
        (_('Donor Information'), {
            'fields': ('donor', 'is_anonymous', 'donor_name', 'donor_email')
        }),
        (_('Payment Verification'), {
            'fields': ('payment_proof', 'gcash_transaction_id', 'verification_notes', 'verified_by', 'verification_date')
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



@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ('donation', 'alert_type', 'severity', 'status', 'created_at', 'reviewed_by')
    list_filter = ('alert_type', 'severity', 'status', 'created_at')
    search_fields = ('donation__reference_number', 'description', 'ip_address')
    readonly_fields = ('created_at', 'metadata')
    fieldsets = (
        (_('Alert Information'), {
            'fields': ('donation', 'alert_type', 'severity', 'status', 'description')
        }),
        (_('Technical Details'), {
            'fields': ('ip_address', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
        (_('Review Information'), {
            'fields': ('reviewed_by', 'reviewed_at', 'resolution_notes')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.reviewed_at:
            readonly.extend(['alert_type', 'severity', 'donation'])
        return readonly


@admin.register(BlacklistedEntity)
class BlacklistedEntityAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'value', 'is_active', 'created_by', 'created_at', 'expires_at')
    list_filter = ('entity_type', 'is_active', 'created_at')
    search_fields = ('value', 'reason')
    readonly_fields = ('created_at',)
    fieldsets = (
        (_('Blacklist Information'), {
            'fields': ('entity_type', 'value', 'reason', 'is_active')
        }),
        (_('Expiration'), {
            'fields': ('expires_at',)
        }),
        (_('System Information'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
