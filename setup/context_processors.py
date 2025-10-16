"""
Context processors for the setup app.
"""
from django.conf import settings


def setup_status(request):
    """
    Add setup status information to template context.
    """
    try:
        from .utils import is_setup_complete, get_setup_progress
        return {
            'setup_complete': is_setup_complete(),
            'setup_progress': get_setup_progress(),
        }
    except Exception:
        # If setup app is not ready, return default values
        return {
            'setup_complete': False,
            'setup_progress': {
                'environment_setup': False,
                'database_available': False,
                'setup_complete': False,
                'overall_progress': 0
            }
        }


def site_config(request):
    """
    Add dynamic site configuration to template context.
    """
    try:
        from .models import SiteConfiguration, FeatureToggle
        
        # Get common site settings
        site_config = {
            'site_name': SiteConfiguration.get_setting('site_name', 'NORSU Alumni System'),
            'site_description': SiteConfiguration.get_setting('site_description', 'Alumni Management System'),
            'admin_email': SiteConfiguration.get_setting('admin_email', 'admin@example.com'),
            'timezone': SiteConfiguration.get_setting('timezone', 'UTC'),
        }
        
        # Get feature toggles
        features = {}
        for feature in FeatureToggle.objects.filter(is_enabled=True):
            features[feature.name] = feature.is_enabled
        
        return {
            'site_config': site_config,
            'features': features,
        }
    except Exception:
        # If models are not ready, return default values
        return {
            'site_config': {
                'site_name': 'NORSU Alumni System',
                'site_description': 'Alumni Management System',
                'admin_email': 'admin@example.com',
                'timezone': 'UTC',
            },
            'features': {},
        }


def setup_navigation(request):
    """
    Add setup navigation information to template context.
    """
    setup_steps = [
        {
            'name': 'welcome',
            'title': 'Welcome',
            'icon': 'fas fa-home',
            'url': 'setup:welcome',
        },
        {
            'name': 'basic_config',
            'title': 'Basic Config',
            'icon': 'fas fa-cog',
            'url': 'setup:basic_config',
        },
        {
            'name': 'email_config',
            'title': 'Email Config',
            'icon': 'fas fa-envelope',
            'url': 'setup:email_config',
        },
        {
            'name': 'superuser_setup',
            'title': 'Admin Account',
            'icon': 'fas fa-user-shield',
            'url': 'setup:superuser_setup',
        },
        {
            'name': 'complete',
            'title': 'Complete',
            'icon': 'fas fa-check',
            'url': 'setup:complete',
        },
    ]
    
    current_step = None
    if hasattr(request, 'resolver_match') and request.resolver_match:
        current_step = request.resolver_match.url_name
    
    return {
        'setup_steps': setup_steps,
        'current_setup_step': current_step,
    }
