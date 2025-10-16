"""
reCAPTCHA Configuration Admin Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models.recaptcha_config import ReCaptchaConfig
import logging

logger = logging.getLogger(__name__)

def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(is_admin)
def recaptcha_configuration_list(request):
    """List all reCAPTCHA configurations"""
    configs = ReCaptchaConfig.objects.all()
    
    context = {
        'configs': configs,
        'page_title': 'reCAPTCHA Configuration',
        'active_config': ReCaptchaConfig.objects.filter(is_active=True).first()
    }
    
    return render(request, 'recaptcha_configuration_list.html', context)

@user_passes_test(is_admin)
def recaptcha_configuration_create(request):
    """Create new reCAPTCHA configuration"""
    if request.method == 'POST':
        try:
            config = ReCaptchaConfig(
                name=request.POST.get('name'),
                site_key=request.POST.get('site_key'),
                secret_key=request.POST.get('secret_key'),
                version='v3',  # Always use v3
                threshold=float(request.POST.get('threshold', 0.5)),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            config.full_clean()
            config.save()
            
            messages.success(request, f'reCAPTCHA configuration "{config.name}" created successfully!')
            return redirect('core:recaptcha_configuration_list')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error creating configuration: {str(e)}')
    
    context = {
        'page_title': 'Create reCAPTCHA Configuration'
    }
    
    return render(request, 'recaptcha_configuration_form.html', context)

@user_passes_test(is_admin)
def recaptcha_configuration_edit(request, config_id):
    """Edit existing reCAPTCHA configuration"""
    config = get_object_or_404(ReCaptchaConfig, id=config_id)
    
    if request.method == 'POST':
        try:
            config.name = request.POST.get('name')
            config.site_key = request.POST.get('site_key')
            config.secret_key = request.POST.get('secret_key')
            config.version = 'v3'  # Always use v3
            config.threshold = float(request.POST.get('threshold', 0.5))
            config.is_active = request.POST.get('is_active') == 'on'
            
            config.full_clean()
            config.save()
            
            messages.success(request, f'reCAPTCHA configuration "{config.name}" updated successfully!')
            return redirect('core:recaptcha_configuration_list')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error updating configuration: {str(e)}')
    
    context = {
        'config': config,
        'page_title': f'Edit {config.name}'
    }
    
    return render(request, 'recaptcha_configuration_form.html', context)

@user_passes_test(is_admin)
@require_POST
def recaptcha_configuration_test(request, config_id):
    """Test reCAPTCHA configuration"""
    config = get_object_or_404(ReCaptchaConfig, id=config_id)
    
    try:
        success, message = config.test_configuration()
        
        # Check if this is an AJAX request
        is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                  request.content_type == 'application/json')
        
        if is_ajax:
            if success:
                return JsonResponse({
                    'success': True,
                    'message': message
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
        else:
            # Regular form submission
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('core:recaptcha_configuration_list')
            
    except Exception as e:
        error_message = f'Test failed: {str(e)}'
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'message': error_message
            })
        else:
            messages.error(request, error_message)
            return redirect('core:recaptcha_configuration_list')

@user_passes_test(is_admin)
@require_POST
def recaptcha_configuration_delete(request, config_id):
    """Delete reCAPTCHA configuration"""
    config = get_object_or_404(ReCaptchaConfig, id=config_id)
    config_name = config.name
    
    try:
        config.delete()
        messages.success(request, f'reCAPTCHA configuration "{config_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting configuration: {str(e)}')
    
    return redirect('core:recaptcha_configuration_list')

@user_passes_test(is_admin)
@require_POST
def recaptcha_configuration_activate(request, config_id):
    """Activate reCAPTCHA configuration"""
    config = get_object_or_404(ReCaptchaConfig, id=config_id)
    
    try:
        # Deactivate all other configurations
        ReCaptchaConfig.objects.filter(is_active=True).update(is_active=False)
        
        # Activate this configuration
        ReCaptchaConfig.objects.filter(pk=config.pk).update(is_active=True)
        
        messages.success(request, f'reCAPTCHA configuration "{config.name}" activated successfully!')
    except Exception as e:
        messages.error(request, f'Error activating configuration: {str(e)}')
    
    return redirect('core:recaptcha_configuration_list')

