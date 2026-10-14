from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Alumni, GraduateRegistry

# Register your models here.

@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'college', 'course', 'graduation_year', 'employment_status', 'mentorship_status', 'is_verified', 'is_featured', 'profile_editor_link')
    list_filter = ('graduation_year', 'college', 'campus', 'employment_status', 'mentorship_status', 'is_verified', 'is_featured')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'course')
    readonly_fields = ('created_at', 'updated_at', 'profile_editor_link')
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
        ('Extended alumni profile', {'fields': ('profile_editor_link',), 'description': 'Additional alumni fields are stored in the associated Profile record to avoid duplicate data.'}),
        ('Metadata', {
            'fields': ('is_verified', 'is_featured', 'created_at', 'updated_at')
        }),
    )

    @admin.display(description='Extended profile')
    def profile_editor_link(self, obj):
        if not obj or not obj.pk:
            return 'Save this alumni record first.'
        try:
            profile = obj.user.profile
        except (AttributeError,):
            return 'No associated profile'
        return format_html('<a href="{}">Edit extended profile</a>',
                           reverse('admin:accounts_profile_change', args=[profile.pk]))

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


@admin.register(GraduateRegistry)
class GraduateRegistryAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'campus', 'graduation_year', 'course', 'claimed_by')
    list_filter = ('campus', 'graduation_year')
    search_fields = ('first_name', 'last_name', 'email', 'course')
    readonly_fields = ('claimed_by', 'imported_at', 'updated_at')
