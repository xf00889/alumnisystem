"""
SSO Configuration Admin Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .models import SSOConfig
import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_admin)
def sso_configuration_list(request):
    """List all SSO configurations"""
    configs = SSOConfig.objects.all()
    
    # Group by provider
    google_configs = configs.filter(provider='google')
    facebook_configs = configs.filter(provider='facebook')
    
    context = {
        'google_configs': google_configs,
        'facebook_configs': facebook_configs,
        'page_title': 'SSO Configuration',
        'active_google': google_configs.filter(is_active=True, enabled=True).first(),
        'active_facebook': facebook_configs.filter(is_active=True, enabled=True).first(),
    }
    
    return render(request, 'sso_configuration_list.html', context)


@user_passes_test(is_admin)
def sso_configuration_create(request):
    """Create new SSO configuration"""
    if request.method == 'POST':
        try:
            config = SSOConfig(
                name=request.POST.get('name'),
                provider=request.POST.get('provider'),
                client_id=request.POST.get('client_id'),
                secret_key=request.POST.get('secret_key'),
                scopes=request.POST.get('scopes', 'profile,email'),
                verified_email=request.POST.get('verified_email') == 'on',
                is_active=request.POST.get('is_active') == 'on',
                enabled=request.POST.get('enabled', 'on') == 'on',
            )
            
            # Validate
            config.full_clean()
            config.save()
            
            messages.success(request, f'SSO configuration "{config.name}" created successfully!')
            
            # Clear any cached SSO settings
            from django.core.cache import cache
            cache.delete('sso_providers_config')
            
            return redirect('core:sso_configuration_list')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error creating configuration: {str(e)}')
            logger.error(f"Error creating SSO configuration: {str(e)}", exc_info=True)
    
    context = {
        'page_title': 'Create SSO Configuration',
        'provider_choices': SSOConfig.PROVIDER_CHOICES,
    }
    
    return render(request, 'sso_configuration_form.html', context)


@user_passes_test(is_admin)
def sso_configuration_edit(request, config_id):
    """Edit existing SSO configuration"""
    config = get_object_or_404(SSOConfig, id=config_id)
    
    if request.method == 'POST':
        try:
            config.name = request.POST.get('name')
            config.provider = request.POST.get('provider')
            config.client_id = request.POST.get('client_id')
            config.secret_key = request.POST.get('secret_key')
            config.scopes = request.POST.get('scopes', 'profile,email')
            config.verified_email = request.POST.get('verified_email') == 'on'
            config.is_active = request.POST.get('is_active') == 'on'
            config.enabled = request.POST.get('enabled', 'on') == 'on'
            
            # Validate
            config.full_clean()
            config.save()
            
            messages.success(request, f'SSO configuration "{config.name}" updated successfully!')
            
            # Clear any cached SSO settings
            from django.core.cache import cache
            cache.delete('sso_providers_config')
            
            return redirect('core:sso_configuration_list')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error updating configuration: {str(e)}')
            logger.error(f"Error updating SSO configuration: {str(e)}", exc_info=True)
    
    context = {
        'config': config,
        'page_title': f'Edit SSO Configuration: {config.name}',
        'provider_choices': SSOConfig.PROVIDER_CHOICES,
    }
    
    return render(request, 'sso_configuration_form.html', context)


@user_passes_test(is_admin)
@require_POST
def sso_configuration_test(request, config_id):
    """Test SSO configuration"""
    config = get_object_or_404(SSOConfig, id=config_id)
    
    try:
        success, message = config.test_configuration()
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
        return redirect('core:sso_configuration_list')
            
    except Exception as e:
        error_message = f'Error testing configuration: {str(e)}'
        logger.error(error_message, exc_info=True)
        messages.error(request, error_message)
        return redirect('core:sso_configuration_list')


@user_passes_test(is_admin)
@require_POST
def sso_configuration_delete(request, config_id):
    """Delete SSO configuration"""
    config = get_object_or_404(SSOConfig, id=config_id)
    config_name = config.name
    
    try:
        config.delete()
        messages.success(request, f'SSO configuration "{config_name}" deleted successfully!')
        
        # Clear any cached SSO settings
        from django.core.cache import cache
        cache.delete('sso_providers_config')
        
    except Exception as e:
        messages.error(request, f'Error deleting configuration: {str(e)}')
        logger.error(f"Error deleting SSO configuration: {str(e)}", exc_info=True)
    
    return redirect('core:sso_configuration_list')


@user_passes_test(is_admin)
@require_POST
def sso_configuration_activate(request, config_id):
    """Activate SSO configuration"""
    config = get_object_or_404(SSOConfig, id=config_id)
    
    try:
        # Deactivate other configs for the same provider
        SSOConfig.objects.filter(provider=config.provider, is_active=True).update(is_active=False)
        
        # Activate this config
        SSOConfig.objects.filter(pk=config.pk).update(is_active=True)
        
        messages.success(request, f'SSO configuration "{config.name}" activated successfully!')
        
        # Clear any cached SSO settings
        from django.core.cache import cache
        cache.delete('sso_providers_config')
        
    except Exception as e:
        messages.error(request, f'Error activating configuration: {str(e)}')
        logger.error(f"Error activating SSO configuration: {str(e)}", exc_info=True)
    
    return redirect('core:sso_configuration_list')


@user_passes_test(is_admin)
@require_POST
def sso_configuration_toggle_enabled(request, config_id):
    """Toggle SSO enabled status"""
    config = get_object_or_404(SSOConfig, id=config_id)
    
    try:
        config.enabled = not config.enabled
        config.save()
        
        status = "enabled" if config.enabled else "disabled"
        messages.success(request, f'SSO provider "{config.name}" {status} successfully!')
        
        # Clear any cached SSO settings
        from django.core.cache import cache
        cache.delete('sso_providers_config')
        
    except Exception as e:
        messages.error(request, f'Error toggling SSO status: {str(e)}')
        logger.error(f"Error toggling SSO status: {str(e)}", exc_info=True)
    
    return redirect('core:sso_configuration_list')
