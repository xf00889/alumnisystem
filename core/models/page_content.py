from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

class PageSection(models.Model):
    """
    Model for managing dynamic content sections across the site
    """
    SECTION_TYPES = [
        ('HERO', 'Hero Section'),
        ('FEATURE', 'Feature Section'),
        ('ABOUT', 'About Section'),
        ('TESTIMONIAL', 'Testimonial Section'),
        ('CTA', 'Call to Action Section'),
        ('STATISTIC', 'Statistics Section'),
        ('FOOTER', 'Footer Section'),
        ('OTHER', 'Other Section'),
    ]
    
    # Alias for compatibility with admin_views.py
    SECTION_TYPE_CHOICES = SECTION_TYPES
    
    PAGE_CHOICES = [
        ('home', _('Home Page')),
        ('about', _('About Page')),
        ('contact', _('Contact Page')),
        ('services', _('Services Page')),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    page = models.CharField(max_length=20, choices=PAGE_CHOICES, default='home')
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES, default='OTHER')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='page_sections/', blank=True, null=True,
                             validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])])
    background_image = models.ImageField(upload_to='page_sections/backgrounds/', blank=True, null=True,
                                        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])])
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Page Section')
        verbose_name_plural = _('Page Sections')
        ordering = ['order', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_section_type_display()})"


class Testimonial(models.Model):
    """
    Model for alumni testimonials displayed on the landing page
    """
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    quote = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True,
                             validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')
        ordering = ['-is_featured', 'order', '-created_at']
        
    def __str__(self):
        return f"Testimonial by {self.name}"


class StaffMember(models.Model):
    """
    Model for staff members displayed on the About Us page
    """
    STAFF_TYPES = [
        ('ADMIN', 'Administrative Staff'),
        ('FACULTY', 'Faculty Member'),
        ('SUPPORT', 'Support Staff'),
        ('LEADERSHIP', 'Leadership Team'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPES, default='OTHER')
    department = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to='staff/', blank=True, null=True,
                             validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Staff Member')
        verbose_name_plural = _('Staff Members')
        ordering = ['staff_type', 'order', 'name']
        
    def __str__(self):
        return f"{self.name} - {self.position}"


class SiteConfiguration(models.Model):
    """
    Model for global site settings and configuration
    """
    site_name = models.CharField(max_length=100, default="NORSU Alumni System")
    site_tagline = models.CharField(max_length=200, blank=True, null=True)
    primary_color = models.CharField(max_length=20, default="#0d6efd")
    secondary_color = models.CharField(max_length=20, default="#6c757d")
    
    # Contact Information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_address = models.TextField(blank=True, null=True)
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    
    # Site Statistics (for hero section)
    alumni_count_override = models.PositiveIntegerField(blank=True, null=True, 
                                                      help_text="Leave blank to use actual count from database")
    groups_count_override = models.PositiveIntegerField(blank=True, null=True,
                                                      help_text="Leave blank to use actual count from database")
    jobs_count_override = models.PositiveIntegerField(blank=True, null=True,
                                                    help_text="Leave blank to use actual count from database")
    
    # Footer Content
    footer_text = models.TextField(blank=True, null=True)
    copyright_text = models.CharField(max_length=200, blank=True, null=True)
    
    # SEO Settings
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    # Misc Settings
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Site Configuration')
        verbose_name_plural = _('Site Configuration')
        
    def __str__(self):
        return "Site Configuration"
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration exists
        if not self.pk and SiteConfiguration.objects.exists():
            return
        super().save(*args, **kwargs)