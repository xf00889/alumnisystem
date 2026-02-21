"""
Context processors for adding global template variables
"""

def user_role_context(request):
    """
    Add user role information to template context
    """
    context = {
        'is_alumni_coordinator': False,
        'can_access_system_config': False,
    }
    
    if request.user.is_authenticated:
        # Check if user is alumni coordinator
        if hasattr(request.user, 'profile'):
            context['is_alumni_coordinator'] = request.user.profile.is_alumni_coordinator
        
        # Only superusers can access system configuration
        context['can_access_system_config'] = request.user.is_superuser
    
    return context


def recaptcha_context(request):
    """
    Add reCAPTCHA configuration to template context
    """
    try:
        from core.recaptcha_utils import get_recaptcha_public_key, get_recaptcha_config
        
        # Get the config to check if reCAPTCHA is enabled
        config = get_recaptcha_config()
        public_key = get_recaptcha_public_key()
        
        return {
            'recaptcha_public_key': public_key if public_key else '',
            'recaptcha_site_key': public_key if public_key else '',  # Alias for compatibility
            'recaptcha_enabled': bool(config and config.enabled) if config else False,
        }
    except Exception:
        # Return empty values if there's an error
        return {
            'recaptcha_public_key': '',
            'recaptcha_site_key': '',
            'recaptcha_enabled': False,
        }


def sso_context(request):
    """
    Add SSO configuration to template context
    """
    try:
        from core.sso_utils import get_enabled_sso_providers
        enabled_providers = get_enabled_sso_providers()
        return {
            'sso_providers': enabled_providers,
            'enabled_sso_providers': enabled_providers,  # Alias for template compatibility
        }
    except Exception:
        return {
            'sso_providers': [],
            'enabled_sso_providers': [],
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
    except Exception:
        return {
            'cms_contact_info': [],
        }


def seo_context(request):
    """
    Add SEO information to template context
    """
    try:
        from core.models.seo import PageSEO, OrganizationSchema
        
        # Get SEO data for current page if available
        path = request.path
        page_seo = PageSEO.objects.filter(page_path=path, is_active=True).first()
        
        # Get organization schema for default values
        org_schema = OrganizationSchema.objects.filter(is_active=True).first()
        
        # Build SEO object with defaults
        seo_data = {
            'title': page_seo.meta_title if page_seo else (org_schema.name if org_schema else 'NORSU Alumni Network'),
            'description': page_seo.meta_description if page_seo else (org_schema.description if org_schema else 'Connect with NORSU alumni, access exclusive opportunities, and stay engaged with the university community.'),
            'keywords': page_seo.meta_keywords if page_seo else 'NORSU, alumni, network, university, graduates',
            'canonical_url': request.build_absolute_uri(path),
            'og_image': page_seo.og_image.url if (page_seo and page_seo.og_image) else (org_schema.logo if org_schema else ''),
            'twitter_image': page_seo.twitter_image.url if (page_seo and page_seo.twitter_image) else '',
            'og_type': page_seo.og_type if page_seo else 'website',
            'site_name': org_schema.name if org_schema else 'NORSU Alumni Network',
        }
        
        return {
            'page_seo': page_seo,
            'seo': seo_data,  # Add this for the template
        }
    except Exception as e:
        # Return default SEO data if there's an error
        return {
            'page_seo': None,
            'seo': {
                'title': 'NORSU Alumni Network',
                'description': 'Connect with NORSU alumni, access exclusive opportunities, and stay engaged with the university community.',
                'keywords': 'NORSU, alumni, network, university, graduates',
                'canonical_url': request.build_absolute_uri(request.path),
                'og_image': '',
                'twitter_image': '',
                'og_type': 'website',
                'site_name': 'NORSU Alumni Network',
            },
        }


def footer_links(request):
    """
    Add footer links to template context
    """
    try:
        from cms.models import FooterLink
        links = FooterLink.objects.filter(is_active=True).order_by('order')
        return {
            'footer_links': links,
        }
    except Exception:
        return {
            'footer_links': [],
        }
