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
    
    # Hero Section Fields
    hero_headline = models.CharField(
        max_length=200,
        default="Advance Your Career With 5,000+ NORSU Professionals",
        help_text=_("Main headline for the hero section (6-10 words recommended)")
    )
    hero_subheadline = models.TextField(
        default="Access exclusive job opportunities, industry mentorship, and a network of alumni leaders across 30+ countries.",
        help_text=_("Subheadline for the hero section (15-25 words recommended)")
    )
    hero_background_image = models.ImageField(
        upload_to='cms/hero/',
        null=True,
        blank=True,
        help_text=_("Background image for the hero section (recommended: 1920x600px, < 500KB)")
    )
    hero_primary_cta_text = models.CharField(
        max_length=100,
        default="Start Your Career Growth",
        help_text=_("Primary CTA button text (2-4 words)")
    )
    hero_secondary_cta_text = models.CharField(
        max_length=100,
        default="Sign In",
        help_text=_("Secondary CTA button text (2-3 words)")
    )
    hero_microcopy = models.CharField(
        max_length=200,
        default="Takes 2 minutes • No credit card required",
        help_text=_("Microcopy text below CTA buttons to reduce friction")
    )
    
    # Hero Social Proof Fields
    hero_alumni_count = models.CharField(
        max_length=50,
        default="5,000+",
        help_text=_("Number of alumni (e.g., '5,000+')")
    )
    hero_opportunities_count = models.CharField(
        max_length=50,
        default="500+",
        help_text=_("Number of career opportunities (e.g., '500+')")
    )
    hero_countries_count = models.CharField(
        max_length=50,
        default="30+",
        help_text=_("Number of countries represented (e.g., '30+')")
    )
    
    # Hero Variant Tracking (for A/B testing)
    hero_variant = models.CharField(
        max_length=50,
        default="variation-1",
        help_text=_("Current hero section variant for A/B testing (e.g., 'variation-1', 'variation-2')")
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
                'hero_headline': 'Advance Your Career With 5,000+ NORSU Professionals',
                'hero_subheadline': 'Access exclusive job opportunities, industry mentorship, and a network of alumni leaders across 30+ countries.',
                'hero_primary_cta_text': 'Start Your Career Growth',
                'hero_secondary_cta_text': 'Sign In',
                'hero_microcopy': 'Takes 2 minutes • No credit card required',
                'hero_alumni_count': '5,000+',
                'hero_opportunities_count': '500+',
                'hero_countries_count': '30+',
                'hero_variant': 'variation-1',
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



class NORSUCampus(TimeStampedModel):
    """
    Model for managing NORSU campuses displayed on homepage slider
    """
    name = models.CharField(
        max_length=200,
        help_text=_("Campus name (e.g., 'Main Campus', 'Bais Campus')")
    )
    location = models.CharField(
        max_length=200,
        help_text=_("Campus location/address")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Brief description of the campus")
    )
    image = models.ImageField(
        upload_to='cms/campuses/',
        help_text=_("Campus photo for slider")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order in slider (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this campus should be displayed in slider")
    )

    class Meta:
        verbose_name = _('NORSU Campus')
        verbose_name_plural = _('NORSU Campuses')
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.location}"


class NORSUOfficial(TimeStampedModel):
    """
    Model for managing NORSU officials from President to lowest rank
    """
    POSITION_LEVEL_CHOICES = [
        (1, _('University President')),
        (2, _('Vice President')),
        (3, _('Dean')),
        (4, _('Associate Dean')),
        (5, _('Director')),
        (6, _('Department Head')),
        (7, _('Other Official')),
    ]

    name = models.CharField(
        max_length=200,
        help_text=_("Full name with title (e.g., 'Dr. John Doe')")
    )
    position = models.CharField(
        max_length=200,
        help_text=_("Official position/title")
    )
    position_level = models.IntegerField(
        choices=POSITION_LEVEL_CHOICES,
        default=7,
        help_text=_("Position level for hierarchical ordering")
    )
    department = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Department, college, or office")
    )
    bio = models.TextField(
        blank=True,
        help_text=_("Brief biography or description")
    )
    image = models.ImageField(
        upload_to='cms/officials/',
        null=True,
        blank=True,
        help_text=_("Official photo")
    )
    email = models.EmailField(
        blank=True,
        help_text=_("Contact email address")
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Contact phone number")
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Display order within position level (lower numbers appear first)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this official should be displayed")
    )

    class Meta:
        verbose_name = _('NORSU Official')
        verbose_name_plural = _('NORSU Officials')
        ordering = ['position_level', 'order', 'name']
        indexes = [
            models.Index(fields=['position_level', 'is_active', 'order']),
        ]

    def __str__(self):
        return f"{self.name} - {self.position}"


class NORSUVMGOHistory(TimeStampedModel):
    """
    Singleton model for managing NORSU Vision, Mission, Goals, Objectives, and History
    """
    # Section Configuration
    section_title = models.CharField(
        max_length=200,
        default="NORSU Vision, Mission, Goals & Core Values",
        help_text=_("Main section title")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Show/hide this section on homepage")
    )
    
    # About NORSU
    about_title = models.CharField(
        max_length=100,
        default="About NORSU",
        help_text=_("Title for About section")
    )
    
    about_content = models.TextField(
        default="Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.",
        help_text=_("Introduction text about NORSU (200-300 words recommended)")
    )
    
    # Vision
    vision_title = models.CharField(
        max_length=100,
        default="NORSU Vision",
        help_text=_("Title for Vision section")
    )
    
    vision = models.TextField(
        default="A globally recognized state university.",
        help_text=_("NORSU Vision statement (50-100 words recommended)")
    )
    
    # Mission
    mission_title = models.CharField(
        max_length=100,
        default="NORSU Mission",
        help_text=_("Title for Mission section")
    )
    
    mission = models.TextField(
        default="Negros Oriental State University delivers global excellence through advanced instruction, impactful research, and sustainable extension, with strategic partnerships and modern infrastructure shaping effective leaders to serve the Philippine society and the world.",
        help_text=_("NORSU Mission statement (100-150 words recommended)")
    )
    
    # Goals
    goals_title = models.CharField(
        max_length=100,
        default="Goals",
        help_text=_("Title for Goals section")
    )
    
    goals = models.TextField(
        default="ASPIRE:\n• Achieve global recognition by program excellence\n• Strengthen research through impactful innovation\n• Promote enhanced community extension services\n• Integrate partnerships and international relations\n• Revitalize infrastructure with operational systems\n• Enrich student life and leadership opportunities",
        help_text=_("NORSU Strategic Goals (supports bullet points)")
    )
    
    # Core Values
    values_title = models.CharField(
        max_length=100,
        default="Core Values",
        help_text=_("Title for Core Values section")
    )
    
    core_values = models.TextField(
        default="SHINE:\n• Spirituality\n• Honesty\n• Innovation\n• Nurturance\n• Excellence",
        help_text=_("NORSU Core Values (supports bullet points)")
    )
    
    quality_policy = models.TextField(
        default="Negros Oriental State University commits to delivering quality instruction, research, extension and production. We ensure compliance with all statutory and regulatory requirements and continuously work to improve our management system to meet our quality objectives.",
        help_text=_("NORSU Quality Policy")
    )
    
    # History
    history_brief = models.TextField(
        default="Negros Oriental State University was established in 1907, when Governor Hermenegildo Villanueva proposed the establishment of industrial arts education in Negros Oriental Provincial School (NOPS), the precursor of the Negros Oriental High School (NOHS).",
        help_text=_("Brief history summary")
    )
    history_full = models.TextField(
        default="The beginnings of Negros Oriental State University date back to 1907, from a single woodworking class at what was then the Negros Oriental Provincial School. On December 3, 1927, by virtue of Act No. 3377 of the Philippine Legislature, the woodworking class became the Negros Oriental Trade School (NOTS). By virtue of Republic Act No. 1579 signed into law on June 16, 1956, NOTS became the East Visayan School of Arts and Trades (EVSAT). Through Batas Pambansa No. 401 signed by President Ferdinand E. Marcos on June 10, 1983, the Central Visayas Polytechnic College (CVPC) came into being. Finally, through Republic Act No. 9299 signed by President Gloria Macapagal Arroyo on June 25, 2004, CVPC was converted into Negros Oriental State University (NORSU).",
        help_text=_("Full detailed history")
    )
    establishment_year = models.CharField(
        max_length=10,
        default="1907",
        help_text=_("Year NORSU was originally established")
    )
    university_status_year = models.CharField(
        max_length=10,
        default="2004",
        help_text=_("Year it became a university")
    )
    
    # Display settings (kept for backward compatibility)
    show_on_homepage = models.BooleanField(
        default=True,
        help_text=_("Display VMGO section on homepage (deprecated, use is_active)")
    )
    show_history_on_homepage = models.BooleanField(
        default=True,
        help_text=_("Display history section on homepage")
    )

    class Meta:
        verbose_name = _('NORSU VMGO & History')
        verbose_name_plural = _('NORSU VMGO & History')

    def __str__(self):
        return f"NORSU VMGO Section - {self.section_title}"

    @classmethod
    def get_vmgo_section(cls):
        """Get or create singleton instance"""
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'section_title': 'NORSU Vision, Mission, Goals & Core Values',
                'is_active': True,
                'about_title': 'About NORSU',
                'about_content': 'Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.',
                'vision_title': 'NORSU Vision',
                'vision': 'A globally recognized state university.',
                'mission_title': 'NORSU Mission',
                'mission': 'Negros Oriental State University delivers global excellence through advanced instruction, impactful research, and sustainable extension, with strategic partnerships and modern infrastructure shaping effective leaders to serve the Philippine society and the world.',
                'goals_title': 'Goals',
                'goals': 'ASPIRE:\n• Achieve global recognition by program excellence\n• Strengthen research through impactful innovation\n• Promote enhanced community extension services\n• Integrate partnerships and international relations\n• Revitalize infrastructure with operational systems\n• Enrich student life and leadership opportunities',
                'values_title': 'Core Values',
                'core_values': 'SHINE:\n• Spirituality\n• Honesty\n• Innovation\n• Nurturance\n• Excellence',
                'quality_policy': 'Negros Oriental State University commits to delivering quality instruction, research, extension and production. We ensure compliance with all statutory and regulatory requirements and continuously work to improve our management system to meet our quality objectives.',
                'history_brief': 'Negros Oriental State University was established in 1907, when Governor Hermenegildo Villanueva proposed the establishment of industrial arts education in Negros Oriental Provincial School (NOPS), the precursor of the Negros Oriental High School (NOHS).',
                'history_full': 'The beginnings of Negros Oriental State University date back to 1907, from a single woodworking class at what was then the Negros Oriental Provincial School. On December 3, 1927, by virtue of Act No. 3377 of the Philippine Legislature, the woodworking class became the Negros Oriental Trade School (NOTS). By virtue of Republic Act No. 1579 signed into law on June 16, 1956, NOTS became the East Visayan School of Arts and Trades (EVSAT). Through Batas Pambansa No. 401 signed by President Ferdinand E. Marcos on June 10, 1983, the Central Visayas Polytechnic College (CVPC) came into being. Finally, through Republic Act No. 9299 signed by President Gloria Macapagal Arroyo on June 25, 2004, CVPC was converted into Negros Oriental State University (NORSU).',
                'establishment_year': '1907',
                'university_status_year': '2004',
                'show_on_homepage': True,
                'show_history_on_homepage': True,
            }
        )
        return obj
    
    # Alias for backward compatibility
    @classmethod
    def get_vmgo_history(cls):
        """Alias for get_vmgo_section() for backward compatibility"""
        return cls.get_vmgo_section()
