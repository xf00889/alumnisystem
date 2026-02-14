from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PageSEO(models.Model):
    """
    Stores SEO configuration for individual pages.
    Provides meta tags, Open Graph data, and sitemap settings.
    """
    CHANGEFREQ_CHOICES = [
        ('always', 'Always'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('never', 'Never'),
    ]
    
    page_path = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("URL path of the page (e.g., '/' or '/about-us/')")
    )
    meta_title = models.CharField(
        max_length=60,
        help_text=_("Page title for search results (50-60 characters recommended)")
    )
    meta_description = models.CharField(
        max_length=160,
        help_text=_("Page description for search results (150-160 characters recommended)")
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Comma-separated keywords")
    )
    og_image = models.ImageField(
        upload_to='seo/og_images/',
        blank=True,
        null=True,
        help_text=_("Open Graph image (1200x630 pixels recommended)")
    )
    twitter_image = models.ImageField(
        upload_to='seo/twitter_images/',
        blank=True,
        null=True,
        help_text=_("Twitter Card image (800x418 pixels recommended)")
    )
    canonical_url = models.URLField(
        blank=True,
        help_text=_("Preferred URL for this page (leave blank to use page_path)")
    )
    sitemap_priority = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.5,
        help_text=_("Priority in sitemap (0.0 to 1.0)")
    )
    sitemap_changefreq = models.CharField(
        max_length=20,
        choices=CHANGEFREQ_CHOICES,
        default='weekly',
        help_text=_("How frequently the page changes")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this SEO configuration is active")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Page SEO")
        verbose_name_plural = _("Page SEO")
        ordering = ['page_path']
    
    def __str__(self):
        return f"{self.page_path} - {self.meta_title}"
    
    def clean(self):
        """
        Validate SEO field constraints.
        """
        errors = {}
        
        # Validate title length (50-60 characters)
        if self.meta_title:
            title_len = len(self.meta_title)
            if title_len < 50 or title_len > 60:
                errors['meta_title'] = ValidationError(
                    _("Meta title should be between 50-60 characters. Current length: %(length)d"),
                    code='invalid_length',
                    params={'length': title_len}
                )
        
        # Validate description length (150-160 characters)
        if self.meta_description:
            desc_len = len(self.meta_description)
            if desc_len < 150 or desc_len > 160:
                errors['meta_description'] = ValidationError(
                    _("Meta description should be between 150-160 characters. Current length: %(length)d"),
                    code='invalid_length',
                    params={'length': desc_len}
                )
        
        # Validate sitemap priority (0.0 to 1.0)
        if self.sitemap_priority is not None:
            if self.sitemap_priority < 0.0 or self.sitemap_priority > 1.0:
                errors['sitemap_priority'] = ValidationError(
                    _("Sitemap priority must be between 0.0 and 1.0"),
                    code='invalid_range'
                )
        
        if errors:
            raise ValidationError(errors)
    
    def get_absolute_url(self):
        """
        Returns the canonical URL or page path.
        """
        return self.canonical_url if self.canonical_url else self.page_path


class OrganizationSchema(models.Model):
    """
    Stores organization structured data for Schema.org markup.
    Used primarily on the About Us page.
    """
    name = models.CharField(
        max_length=255,
        help_text=_("Organization name")
    )
    logo = models.URLField(
        help_text=_("URL to organization logo")
    )
    url = models.URLField(
        help_text=_("Organization website URL")
    )
    telephone = models.CharField(
        max_length=50,
        help_text=_("Contact telephone number")
    )
    email = models.EmailField(
        help_text=_("Contact email address")
    )
    street_address = models.CharField(
        max_length=255,
        help_text=_("Street address")
    )
    address_locality = models.CharField(
        max_length=100,
        help_text=_("City or locality")
    )
    address_region = models.CharField(
        max_length=100,
        help_text=_("State, province, or region")
    )
    postal_code = models.CharField(
        max_length=20,
        help_text=_("Postal or ZIP code")
    )
    address_country = models.CharField(
        max_length=2,
        help_text=_("Country code (ISO 3166-1 alpha-2, e.g., 'PH')")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this organization schema is active")
    )
    
    class Meta:
        verbose_name = _("Organization Schema")
        verbose_name_plural = _("Organization Schemas")
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Validate organization schema fields.
        """
        errors = {}
        
        # Validate country code length (should be 2 characters)
        if self.address_country and len(self.address_country) != 2:
            errors['address_country'] = ValidationError(
                _("Country code must be 2 characters (ISO 3166-1 alpha-2)"),
                code='invalid_length'
            )
        
        if errors:
            raise ValidationError(errors)
    
    def to_json_ld(self):
        """
        Returns JSON-LD formatted structured data for Schema.org Organization.
        """
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.name,
            "logo": self.logo,
            "url": self.url,
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": self.telephone,
                "email": self.email,
                "contactType": "customer service"
            },
            "address": {
                "@type": "PostalAddress",
                "streetAddress": self.street_address,
                "addressLocality": self.address_locality,
                "addressRegion": self.address_region,
                "postalCode": self.postal_code,
                "addressCountry": self.address_country
            }
        }
