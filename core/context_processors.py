"""
Context processors for the core app
"""
from .recaptcha_utils import get_recaptcha_public_key, is_recaptcha_enabled


# Default SEO configuration for high-priority pages
DEFAULT_SEO_CONFIG = {
    '/': {
        'title': 'NORSU Alumni System - Connect, Network, and Grow Together',
        'description': 'Official alumni platform for Negros Oriental State University. Connect with fellow alumni, find mentors, discover career opportunities, and stay updated.',
        'keywords': 'NORSU, alumni, Negros Oriental State University, networking, mentorship, jobs, events',
        'priority': 1.0,
        'changefreq': 'daily',
    },
    '/about-us/': {
        'title': 'About Us - NORSU Alumni System | Our Mission and Vision',
        'description': 'Learn about the NORSU Alumni System, our mission to connect graduates worldwide, and how we support the NORSU community through networking and opportunities.',
        'keywords': 'NORSU, about, mission, vision, alumni association',
        'priority': 0.9,
        'changefreq': 'monthly',
    },
    '/contact-us/': {
        'title': 'Contact Us - NORSU Alumni System | Get in Touch with Us',
        'description': 'Get in touch with the NORSU Alumni System. Find our contact information, office location, email address, and phone number. Send us your inquiries today.',
        'keywords': 'NORSU, contact, email, phone, address, support',
        'priority': 0.8,
        'changefreq': 'monthly',
    },
    '/landing/events/': {
        'title': 'Alumni Events - NORSU Alumni System | Upcoming Gatherings',
        'description': 'Discover upcoming NORSU alumni events, reunions, networking sessions, and professional development workshops. RSVP today and connect with fellow alumni.',
        'keywords': 'NORSU, events, reunions, networking, workshops, alumni gatherings',
        'priority': 0.9,
        'changefreq': 'daily',
    },
    '/jobs/careers/': {
        'title': 'Career Opportunities - NORSU Alumni Job Board | Find Jobs',
        'description': 'Explore career opportunities posted by NORSU alumni and partner organizations. Find jobs, internships, and professional opportunities in your field today.',
        'keywords': 'NORSU, jobs, careers, employment, opportunities, job board',
        'priority': 0.9,
        'changefreq': 'daily',
    },
}


def recaptcha_context(request):
    """
    Add reCAPTCHA configuration to template context
    """
    return {
        'recaptcha_public_key': get_recaptcha_public_key(),
        'recaptcha_enabled': is_recaptcha_enabled(),
    }


def cms_contact_info(request):
    """
    Add CMS contact information to template context
    """
    try:
        from cms.models import ContactInfo
        contact_info = ContactInfo.objects.filter(is_active=True).order_by('contact_type', 'order')
        return {
            'cms_contact_info': contact_info,
        }
    except (ImportError, Exception):
        return {
            'cms_contact_info': [],
        }


def footer_links(request):
    """
    Add dynamic footer links to template context
    """
    try:
        from cms.models import FooterLink
        
        # Get all active footer links grouped by section
        quick_links = FooterLink.objects.filter(
            section='quick_links',
            is_active=True
        ).order_by('order')
        
        information_links = FooterLink.objects.filter(
            section='information',
            is_active=True
        ).order_by('order')
        
        legal_links = FooterLink.objects.filter(
            section='legal',
            is_active=True
        ).order_by('order')
        
        resources_links = FooterLink.objects.filter(
            section='resources',
            is_active=True
        ).order_by('order')
        
        return {
            'footer_quick_links': quick_links,
            'footer_information_links': information_links,
            'footer_legal_links': legal_links,
            'footer_resources_links': resources_links,
        }
    except (ImportError, Exception):
        return {
            'footer_quick_links': [],
            'footer_information_links': [],
            'footer_legal_links': [],
            'footer_resources_links': [],
        }



def get_og_type(page_path):
    """
    Returns the appropriate Open Graph type based on page path.
    
    Args:
        page_path: The URL path of the page
        
    Returns:
        str: The Open Graph type (e.g., 'website', 'article')
    """
    # Map specific paths to Open Graph types
    og_type_map = {
        '/': 'website',
        '/about-us/': 'website',
        '/contact-us/': 'website',
        '/landing/events/': 'website',
        '/jobs/careers/': 'website',
    }
    
    # Return mapped type or default to 'website'
    return og_type_map.get(page_path, 'website')


def get_default_seo(page_path):
    """
    Creates a PageSEO-like object from default configuration.
    
    Args:
        page_path: The URL path of the page
        
    Returns:
        object: A simple object with SEO attributes matching PageSEO model
    """
    from types import SimpleNamespace
    
    # Get default config for this page or use generic defaults
    defaults = DEFAULT_SEO_CONFIG.get(page_path, {
        'title': 'NORSU Alumni System',
        'description': 'Official alumni platform for Negros Oriental State University. Connect with fellow alumni, find mentors, discover jobs, and stay updated with events.',
        'keywords': 'NORSU, alumni, Negros Oriental State University',
        'priority': 0.5,
        'changefreq': 'weekly',
    })
    
    # Create a simple namespace object that mimics PageSEO model
    return SimpleNamespace(
        page_path=page_path,
        meta_title=defaults['title'],
        meta_description=defaults['description'],
        meta_keywords=defaults['keywords'],
        og_image=None,
        twitter_image=None,
        canonical_url='',
        sitemap_priority=defaults['priority'],
        sitemap_changefreq=defaults['changefreq'],
        is_active=True,
        get_absolute_url=lambda: page_path
    )



def seo_context(request):
    """
    Injects SEO data into template context for all pages.
    
    This context processor queries the PageSEO model for the current page
    and falls back to default values if no database entry exists.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Dictionary containing SEO data for templates
    """
    try:
        from core.models.seo import PageSEO
        
        page_path = request.path
        
        # Try to get PageSEO from database
        try:
            page_seo = PageSEO.objects.get(page_path=page_path, is_active=True)
        except PageSEO.DoesNotExist:
            # Fall back to default configuration
            page_seo = get_default_seo(page_path)
        
        # Build the full URL for canonical and social media
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        canonical_url = page_seo.get_absolute_url()
        
        # If canonical_url is relative, make it absolute
        if canonical_url and not canonical_url.startswith('http'):
            canonical_url = f"{scheme}://{host}{canonical_url}"
        
        # Get image URLs (handle both ImageField and None)
        og_image_url = None
        twitter_image_url = None
        
        if hasattr(page_seo, 'og_image') and page_seo.og_image:
            if hasattr(page_seo.og_image, 'url'):
                og_image_url = request.build_absolute_uri(page_seo.og_image.url)
        
        if hasattr(page_seo, 'twitter_image') and page_seo.twitter_image:
            if hasattr(page_seo.twitter_image, 'url'):
                twitter_image_url = request.build_absolute_uri(page_seo.twitter_image.url)
        
        # Return SEO context dictionary
        return {
            'seo': {
                'title': page_seo.meta_title,
                'description': page_seo.meta_description,
                'keywords': page_seo.meta_keywords,
                'canonical_url': canonical_url,
                'og_image': og_image_url,
                'twitter_image': twitter_image_url,
                'site_name': 'NORSU Alumni System',
                'og_type': get_og_type(page_path),
            }
        }
    except Exception as e:
        # If anything goes wrong, return minimal SEO context
        # This prevents template rendering failures
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in seo_context: {e}")
        
        return {
            'seo': {
                'title': 'NORSU Alumni System',
                'description': 'Official alumni platform for Negros Oriental State University.',
                'keywords': 'NORSU, alumni',
                'canonical_url': '',
                'og_image': None,
                'twitter_image': None,
                'site_name': 'NORSU Alumni System',
                'og_type': 'website',
            }
        }
