from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import TimeStampedModel


class SiteConfig(TimeStampedModel):
    """
    Singleton model for global site configuration
    """
    site_name = models.CharField(
        max_length=200,
        default="NORSU Alumni Network",
        help_text=_("The name of the website")
    )
    site_tagline = models.TextField(
        default="Connect. Grow. Succeed.",
        help_text=_("The main tagline displayed on the homepage")
    )
    logo = models.ImageField(
        upload_to='cms/logos/',
        null=True,
        blank=True,
        help_text=_("Site logo image")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        default="alumni@norsu.edu.ph",
        help_text=_("Primary contact email address")
    )
    contact_phone = models.CharField(
        max_length=50,
        default="+63 35 422 6002",
        help_text=_("Primary contact phone number")
    )
    contact_address = models.TextField(
        default="Negros Oriental State University\nKagawasan, Ave. Rizal\nDumaguete City, 6200\nNegros Oriental, Philippines",
        help_text=_("Primary contact address")
    )
    
    # Social Media Links
    facebook_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Facebook page URL")
    )
    twitter_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Twitter profile URL")
    )
    linkedin_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("LinkedIn page URL")
    )
    instagram_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Instagram profile URL")
    )
    youtube_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("YouTube channel URL")
    )
    
    # Button Texts
    signup_button_text = models.CharField(
        max_length=100,
        default="Join the Network",
        help_text=_("Text for the signup button")
    )
    login_button_text = models.CharField(
        max_length=100,
        default="Member Login",
        help_text=_("Text for the login button")
    )

    class Meta:
        verbose_name = _('Site Configuration')
        verbose_name_plural = _('Site Configuration')
        ordering = ['-created']

    def __str__(self):
        return f"Site Configuration - {self.site_name}"

    @classmethod
    def get_site_config(cls):
        """Get or create the singleton site configuration"""
        obj, created = cls.objects.get_or_create(
            defaults={
                'site_name': 'NORSU Alumni Network',
                'site_tagline': 'Connect. Grow. Succeed.',
                'contact_email': 'alumni@norsu.edu.ph',
                'contact_phone': '+63 35 422 6002',
                'contact_address': 'Negros Oriental State University\nKagawasan, Ave. Rizal\nDumaguete City, 6200\nNegros Oriental, Philippines',
                'signup_button_text': 'Join the Network',
                'login_button_text': 'Member Login',
            }
        )
        return obj


class PageSection(TimeStampedModel):
    """
    Model for managing different sections of pages (hero, features, testimonials, etc.)
    """
    SECTION_TYPE_CHOICES = [
        ('hero', _('Hero Section')),
        ('features', _('Features Section')),
        ('testimonials', _('Testimonials Section')),
        ('cta', _('Call to Action Section')),
        ('announcements', _('Announcements Section')),
        ('stats', _('Statistics Section')),
    ]

    section_type = models.CharField(
        max_length=20,
        choices=SECTION_TYPE_CHOICES,
        help_text=_("Type of section")
    )
    title = models.CharField(
        max_length=200,
        help_text=_("Section title")
    )
    subtitle = models.TextField(
        blank=True,
        help_text=_("Section subtitle or description")
    )
    content = models.TextField(
        blank=True,
        help_text=_("Section content (HTML allowed)")
    )
    image = models.ImageField(
        upload_to='cms/sections/',
        null=True,
        blank=True,
        help_text=_("Section image")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this section is active and should be displayed")
    )

    class Meta:
        verbose_name = _('Page Section')
        verbose_name_plural = _('Page Sections')
        ordering = ['order', '-created']
        indexes = [
            models.Index(fields=['section_type', 'is_active']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.get_section_type_display()} - {self.title}"


class StaticPage(TimeStampedModel):
    """
    Model for managing static pages like About, Contact, Privacy Policy, etc.
    """
    PAGE_TYPE_CHOICES = [
        ('about', _('About Us')),
        ('contact', _('Contact Us')),
        ('privacy', _('Privacy Policy')),
        ('terms', _('Terms of Service')),
        ('faq', _('FAQ')),
        ('help', _('Help')),
    ]

    page_type = models.CharField(
        max_length=20,
        choices=PAGE_TYPE_CHOICES,
        unique=True,
        help_text=_("Type of page")
    )
    title = models.CharField(
        max_length=200,
        help_text=_("Page title")
    )
    content = models.TextField(
        help_text=_("Page content (HTML allowed)")
    )
    meta_description = models.TextField(
        blank=True,
        max_length=160,
        help_text=_("Meta description for SEO")
    )
    is_published = models.BooleanField(
        default=True,
        help_text=_("Whether this page is published and visible")
    )

    class Meta:
        verbose_name = _('Static Page')
        verbose_name_plural = _('Static Pages')
        ordering = ['page_type']

    def __str__(self):
        return f"{self.get_page_type_display()} - {self.title}"


class StaffMember(TimeStampedModel):
    """
    Model for managing staff members displayed on About page
    """
    name = models.CharField(
        max_length=200,
        help_text=_("Full name of the staff member")
    )
    position = models.CharField(
        max_length=200,
        help_text=_("Job title or position")
    )
    department = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Department or division")
    )
    bio = models.TextField(
        blank=True,
        help_text=_("Brief biography or description")
    )
    image = models.ImageField(
        upload_to='cms/staff/',
        null=True,
        blank=True,
        help_text=_("Staff member photo")
    )
    email = models.EmailField(
        blank=True,
        help_text=_("Contact email address")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this staff member should be displayed")
    )

    class Meta:
        verbose_name = _('Staff Member')
        verbose_name_plural = _('Staff Members')
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.position}"


# Signal to automatically sync site config tagline with hero section title
@receiver(post_save, sender=SiteConfig)
def sync_site_tagline_with_hero(sender, instance, **kwargs):
    """
    Automatically sync the site config tagline with the hero section title
    """
    try:
        hero_section = PageSection.objects.filter(
            section_type='hero', 
            is_active=True
        ).first()
        
        if hero_section and hero_section.title != instance.site_tagline:
            hero_section.title = instance.site_tagline
            hero_section.save(update_fields=['title', 'modified'])
    except Exception as e:
        # Log the error but don't break the site config save
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to sync hero section title: {e}")


class TimelineItem(TimeStampedModel):
    """
    Model for managing timeline items on About page
    """
    year = models.CharField(
        max_length=10,
        help_text=_("Year or date of the event")
    )
    title = models.CharField(
        max_length=200,
        help_text=_("Title of the timeline event")
    )
    description = models.TextField(
        help_text=_("Description of the event")
    )
    icon = models.CharField(
        max_length=50,
        default="fas fa-circle",
        help_text=_("Font Awesome icon class")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this timeline item should be displayed")
    )

    class Meta:
        verbose_name = _('Timeline Item')
        verbose_name_plural = _('Timeline Items')
        ordering = ['order', 'year']

    def __str__(self):
        return f"{self.year} - {self.title}"


class ContactInfo(TimeStampedModel):
    """
    Model for managing contact information on Contact page
    """
    CONTACT_TYPE_CHOICES = [
        ('phone', _('Phone Number')),
        ('email', _('Email Address')),
        ('address', _('Physical Address')),
        ('hours', _('Office Hours')),
        ('social', _('Social Media')),
    ]

    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        help_text=_("Type of contact information")
    )
    value = models.TextField(
        help_text=_("Contact information value")
    )
    is_primary = models.BooleanField(
        default=False,
        help_text=_("Whether this is the primary contact of this type")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this contact info should be displayed")
    )

    class Meta:
        verbose_name = _('Contact Information')
        verbose_name_plural = _('Contact Information')
        ordering = ['contact_type', 'order']

    def __str__(self):
        return f"{self.get_contact_type_display()} - {self.value[:50]}"


class FAQ(TimeStampedModel):
    """
    Model for managing FAQ items on Contact page
    """
    question = models.CharField(
        max_length=500,
        help_text=_("FAQ question")
    )
    answer = models.TextField(
        help_text=_("FAQ answer")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this FAQ should be displayed")
    )

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['order', 'question']

    def __str__(self):
        return f"Q: {self.question[:50]}"


class Feature(TimeStampedModel):
    """
    Model for managing feature items on the homepage
    """
    title = models.CharField(
        max_length=200,
        help_text=_("Feature title")
    )
    content = models.TextField(
        help_text=_("Feature description")
    )
    icon = models.CharField(
        max_length=50,
        default="fas fa-lightbulb",
        help_text=_("Font Awesome icon class")
    )
    icon_class = models.CharField(
        max_length=50,
        default="info",
        help_text=_("CSS class for icon styling")
    )
    link_url = models.URLField(
        blank=True,
        help_text=_("Optional link URL")
    )
    link_text = models.CharField(
        max_length=100,
        default="Learn More",
        help_text=_("Link text")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this feature should be displayed")
    )

    class Meta:
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')
        ordering = ['order', 'title']

    def __str__(self):
        return f"{self.title}"


class Testimonial(TimeStampedModel):
    """
    Model for managing testimonials on the homepage
    """
    name = models.CharField(
        max_length=200,
        help_text=_("Name of the person giving the testimonial")
    )
    position = models.CharField(
        max_length=200,
        help_text=_("Job title or position")
    )
    company = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Company or organization")
    )
    quote = models.TextField(
        help_text=_("Testimonial quote")
    )
    image = models.ImageField(
        upload_to='cms/testimonials/',
        null=True,
        blank=True,
        help_text=_("Photo of the person")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this testimonial should be displayed")
    )

    class Meta:
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.position}"


# Signal to automatically sync site config tagline with hero section title
@receiver(post_save, sender=SiteConfig)
def sync_site_tagline_with_hero(sender, instance, **kwargs):
    """
    Automatically sync the site config tagline with the hero section title
    """
    try:
        hero_section = PageSection.objects.filter(
            section_type='hero', 
            is_active=True
        ).first()
        
        if hero_section and hero_section.title != instance.site_tagline:
            hero_section.title = instance.site_tagline
            hero_section.save(update_fields=['title', 'modified'])
    except Exception as e:
        # Log the error but don't break the site config save
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to sync hero section title: {e}")