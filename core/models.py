from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models.contact import Address, ContactInfo
from .models.engagement import UserEngagement, EngagementScore

__all__ = [
    'Address',
    'ContactInfo',
    'UserEngagement',
    'EngagementScore',
    'SiteConfiguration',
    'PageSection',
    'Testimonial',
    'StaffMember'
]

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created' and 'modified' fields.
    """
    created = models.DateTimeField(
        _("Created"),
        auto_now_add=True,
        editable=False,
        help_text=_("The date and time this object was created.")
    )
    modified = models.DateTimeField(
        _("Modified"),
        auto_now=True,
        help_text=_("The date and time this object was last modified.")
    )

    class Meta:
        abstract = True
        ordering = ["-created"]

class UserEngagement(TimeStampedModel):
    """
    Model to track user engagement activities
    """
    ACTIVITY_TYPES = [
        ('login', _('Login')),
        ('profile_update', _('Profile Update')),
        ('group_join', _('Group Join')),
        ('group_post', _('Group Post')),
        ('event_rsvp', _('Event RSVP')),
        ('feedback', _('Feedback Submission')),
        ('document_upload', _('Document Upload')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagements'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES
    )
    points = models.PositiveIntegerField(
        default=1,
        help_text=_("Points earned for this activity")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Optional description of the engagement activity")
    )

    class Meta:
        ordering = ['-created']
        verbose_name = _('User Engagement')
        verbose_name_plural = _('User Engagements')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_activity_type_display()}"

class EngagementScore(TimeStampedModel):
    """
    Model to track total engagement scores for users
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_score'
    )
    total_points = models.PositiveIntegerField(
        default=0,
        help_text=_("Total engagement points earned")
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text=_("User engagement level")
    )
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp of last engagement activity")
    )

    class Meta:
        ordering = ['-total_points']
        verbose_name = _('Engagement Score')
        verbose_name_plural = _('Engagement Scores')

    def __str__(self):
        return f"{self.user.get_full_name()} - Level {self.level} ({self.total_points} points)"


class SiteConfiguration(TimeStampedModel):
    """
    Model to store site-wide configuration settings
    """
    site_name = models.CharField(
        max_length=100,
        default="Alumni System",
        help_text=_("Name of the website")
    )
    site_description = models.TextField(
        blank=True,
        help_text=_("Brief description of the website")
    )
    contact_email = models.EmailField(
        blank=True,
        help_text=_("Main contact email address")
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Main contact phone number")
    )
    address = models.TextField(
        blank=True,
        help_text=_("Physical address")
    )
    facebook_url = models.URLField(
        blank=True,
        help_text=_("Facebook page URL")
    )
    twitter_url = models.URLField(
        blank=True,
        help_text=_("Twitter profile URL")
    )
    linkedin_url = models.URLField(
        blank=True,
        help_text=_("LinkedIn profile URL")
    )
    instagram_url = models.URLField(
        blank=True,
        help_text=_("Instagram profile URL")
    )

    class Meta:
        verbose_name = _('Site Configuration')
        verbose_name_plural = _('Site Configurations')

    def __str__(self):
        return self.site_name

    @classmethod
    def get_config(cls):
        """Get or create the site configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class PageSection(TimeStampedModel):
    """
    Model for dynamic page sections
    """
    SECTION_TYPES = [
        ('hero', _('Hero Section')),
        ('about', _('About Section')),
        ('features', _('Features Section')),
        ('testimonials', _('Testimonials Section')),
        ('contact', _('Contact Section')),
        ('custom', _('Custom Section')),
    ]

    PAGE_CHOICES = [
        ('home', _('Home Page')),
        ('about', _('About Page')),
        ('contact', _('Contact Page')),
        ('services', _('Services Page')),
    ]

    title = models.CharField(
        max_length=200,
        help_text=_("Section title")
    )
    content = models.TextField(
        help_text=_("Section content (HTML allowed)")
    )
    page = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        default='home',
        help_text=_("Page where this section appears")
    )
    section_type = models.CharField(
        max_length=50,
        choices=SECTION_TYPES,
        default='custom',
        help_text=_("Type of section")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this section is displayed")
    )

    class Meta:
        ordering = ['page', 'order']
        verbose_name = _('Page Section')
        verbose_name_plural = _('Page Sections')

    def __str__(self):
        return f"{self.get_page_display()} - {self.title}"


class Testimonial(TimeStampedModel):
    """
    Model for customer testimonials
    """
    name = models.CharField(
        max_length=100,
        help_text=_("Customer name")
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Job title or position")
    )
    company = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Company or organization")
    )
    content = models.TextField(
        help_text=_("Testimonial content")
    )
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Whether this testimonial is featured")
    )

    class Meta:
        ordering = ['-is_featured', '-created']
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')

    def __str__(self):
        return f"{self.name} - {self.company}"


class StaffMember(TimeStampedModel):
    """
    Model for staff members
    """
    name = models.CharField(
        max_length=100,
        help_text=_("Staff member name")
    )
    position = models.CharField(
        max_length=100,
        help_text=_("Job title or position")
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Department or division")
    )
    bio = models.TextField(
        blank=True,
        help_text=_("Biography or description")
    )
    email = models.EmailField(
        blank=True,
        help_text=_("Email address")
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Phone number")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this staff member is active")
    )

    class Meta:
        ordering = ['position', 'name']
        verbose_name = _('Staff Member')
        verbose_name_plural = _('Staff Members')

    def __str__(self):
        return f"{self.name} - {self.position}"