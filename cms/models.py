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


class AboutPageConfig(TimeStampedModel):
    """
    Model for managing About page configuration
    """
    # University Information
    university_name = models.CharField(
        max_length=200,
        default="Negros Oriental State University",
        help_text=_("Full name of the university")
    )
    university_short_name = models.CharField(
        max_length=50,
        default="NORSU",
        help_text=_("Short name or acronym")
    )
    university_description = models.TextField(
        default="Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.",
        help_text=_("Main description of the university")
    )
    university_extended_description = models.TextField(
        default="Established in 2004 through the merger of several educational institutions, NORSU has grown to become a leading center of learning in the Visayas region. Our university is dedicated to developing competent professionals who contribute to national development and global competitiveness.",
        help_text=_("Extended description of the university")
    )
    establishment_year = models.CharField(
        max_length=10,
        default="2004",
        help_text=_("Year the university was established")
    )
    
    # Mission and Vision
    mission = models.TextField(
        default="To provide quality and relevant education through instruction, research, extension, and production services for the holistic development of individuals and communities towards a progressive society.",
        help_text=_("University mission statement")
    )
    vision = models.TextField(
        default="A premier state university in the Asia-Pacific region recognized for excellence in instruction, research, extension, and production that produces globally competitive graduates and empowered communities.",
        help_text=_("University vision statement")
    )
    
    # Page Titles
    about_page_title = models.CharField(
        max_length=200,
        default="About NORSU Alumni Network",
        help_text=_("Title for the About page")
    )
    about_page_subtitle = models.TextField(
        default="Learn more about our university, mission, and the people behind our alumni community",
        help_text=_("Subtitle for the About page")
    )
    
    class Meta:
        verbose_name = _('About Page Configuration')
        verbose_name_plural = _('About Page Configuration')

    def __str__(self):
        return f"About Page Config - {self.university_short_name}"

    @classmethod
    def get_about_config(cls):
        """Get or create the singleton about page configuration"""
        obj, created = cls.objects.get_or_create(
            defaults={
                'university_name': 'Negros Oriental State University',
                'university_short_name': 'NORSU',
                'university_description': 'Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.',
                'university_extended_description': 'Established in 2004 through the merger of several educational institutions, NORSU has grown to become a leading center of learning in the Visayas region. Our university is dedicated to developing competent professionals who contribute to national development and global competitiveness.',
                'establishment_year': '2004',
                'mission': 'To provide quality and relevant education through instruction, research, extension, and production services for the holistic development of individuals and communities towards a progressive society.',
                'vision': 'A premier state university in the Asia-Pacific region recognized for excellence in instruction, research, extension, and production that produces globally competitive graduates and empowered communities.',
                'about_page_title': 'About NORSU Alumni Network',
                'about_page_subtitle': 'Learn more about our university, mission, and the people behind our alumni community',
            }
        )
        return obj


class AlumniStatistic(TimeStampedModel):
    """
    Model for managing alumni network statistics
    """
    STATISTIC_TYPES = [
        ('alumni_members', _('Alumni Members')),
        ('alumni_groups', _('Alumni Groups')),
        ('annual_events', _('Annual Events')),
        ('job_opportunities', _('Job Opportunities')),
        ('mentors', _('Mentors')),
        ('scholarships', _('Scholarships')),
        ('countries', _('Countries Represented')),
        ('industries', _('Industries Represented')),
    ]

    statistic_type = models.CharField(
        max_length=30,
        choices=STATISTIC_TYPES,
        help_text=_("Type of statistic")
    )
    value = models.CharField(
        max_length=20,
        help_text=_("Statistic value (e.g., '5,000+', '25+')")
    )
    label = models.CharField(
        max_length=100,
        help_text=_("Display label for the statistic")
    )
    icon = models.CharField(
        max_length=50,
        default="fas fa-users",
        help_text=_("Font Awesome icon class")
    )
    icon_color = models.CharField(
        max_length=7,
        default="#007bff",
        help_text=_("Hex color code for the icon (e.g., #007bff)")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this statistic should be displayed")
    )

    class Meta:
        verbose_name = _('Alumni Statistic')
        verbose_name_plural = _('Alumni Statistics')
        ordering = ['order', 'statistic_type']

    def __str__(self):
        return f"{self.get_statistic_type_display()} - {self.value}"


class FooterLink(TimeStampedModel):
    """
    Model for managing footer links dynamically
    """
    LINK_SECTION_CHOICES = [
        ('quick_links', _('Quick Links')),
        ('information', _('Information')),
        ('legal', _('Legal')),
        ('resources', _('Resources')),
    ]

    title = models.CharField(
        max_length=100,
        help_text=_("Link text to display")
    )
    url = models.CharField(
        max_length=500,
        help_text=_("URL or Django URL name (e.g., 'core:home' or '/about/')")
    )
    section = models.CharField(
        max_length=20,
        choices=LINK_SECTION_CHOICES,
        default='information',
        help_text=_("Which footer section this link belongs to")
    )
    icon = models.CharField(
        max_length=50,
        default="fas fa-link",
        help_text=_("Font Awesome icon class (e.g., 'fas fa-home')")
    )
    open_in_new_tab = models.BooleanField(
        default=False,
        help_text=_("Open link in a new browser tab")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order within section (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this link should be displayed")
    )

    class Meta:
        verbose_name = _('Footer Link')
        verbose_name_plural = _('Footer Links')
        ordering = ['section', 'order', 'title']
        indexes = [
            models.Index(fields=['section', 'is_active', 'order']),
        ]

    def __str__(self):
        return f"{self.get_section_display()} - {self.title}"

    def get_url(self):
        """
        Get the actual URL, handling both Django URL names and direct URLs
        """
        from django.urls import reverse, NoReverseMatch
        
        # If it starts with http:// or https://, it's an external URL
        if self.url.startswith('http://') or self.url.startswith('https://'):
            return self.url
        
        # If it starts with /, it's a direct path
        if self.url.startswith('/'):
            return self.url
        
        # Try to reverse it as a Django URL name
        try:
            return reverse(self.url)
        except NoReverseMatch:
            # If reverse fails, return as-is
            return self.url


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