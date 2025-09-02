from django.contrib import admin
from .models import Alumni

# Register your models here.

@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'college', 'course', 'graduation_year', 'employment_status', 'mentorship_status', 'is_verified', 'is_featured')
    list_filter = ('graduation_year', 'college', 'campus', 'employment_status', 'mentorship_status', 'is_verified', 'is_featured')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'course')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['feature_alumni', 'unfeature_alumni']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'gender', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'alternate_email', 'linkedin_profile')
        }),
        ('Location', {
            'fields': ('country', 'province', 'city', 'address')
        }),
        ('Academic Information', {
            'fields': ('college', 'campus', 'graduation_year', 'course', 'major', 'honors', 'thesis_title')
        }),
        ('Professional Information', {
            'fields': ('current_company', 'job_title', 'employment_status', 'industry')
        }),
        ('Skills & Interests', {
            'fields': ('skills', 'interests')
        }),
        ('Additional Information', {
            'fields': ('bio', 'achievements')
        }),
        ('Mentorship', {
            'fields': ('mentorship_status',)
        }),
        ('Metadata', {
            'fields': ('is_verified', 'is_featured', 'created_at', 'updated_at')
        }),
    )

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.admin_order_field = 'user__last_name'
    full_name.short_description = 'Name'

    def email(self, obj):
        return obj.user.email
    email.admin_order_field = 'user__email'
    email.short_description = 'Email'

    def feature_alumni(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} alumni have been featured on the homepage.")
    feature_alumni.short_description = "Feature selected alumni on homepage"

    def unfeature_alumni(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} alumni have been removed from homepage features.")
    unfeature_alumni.short_description = "Remove selected alumni from homepage features"
