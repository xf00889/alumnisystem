"""
SMTP Configuration Admin Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import SMTPConfig
import logging

logger = logging.getLogger(__name__)

def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(is_admin)
def smtp_configuration_list(request):
    """List all SMTP configurations"""
    configs = SMTPConfig.objects.all()
    
    context = {
        'configs': configs,
        'page_title': 'SMTP Configuration',
        'active_config': SMTPConfig.objects.filter(is_active=True).first()
    }
    
    return render(request, 'smtp_configuration_list.html', context)

@user_passes_test(is_admin)
def smtp_configuration_create(request):
    """Create new SMTP configuration"""
    if request.method == 'POST':
        try:
            config = SMTPConfig(
                name=request.POST.get('name'),
                host=request.POST.get('host'),
                port=int(request.POST.get('port', 587)),
                use_tls=request.POST.get('use_tls') == 'on',
                use_ssl=request.POST.get('use_ssl') == 'on',
                username=request.POST.get('username'),
                password=request.POST.get('password'),
                from_email=request.POST.get('from_email'),
                from_name=request.POST.get('from_name', ''),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            config.full_clean()
            config.save()
            
            # Clear SMTP cache to ensure new settings are loaded
            from .smtp_settings import clear_smtp_cache
            clear_smtp_cache()
            
            messages.success(request, f'SMTP configuration "{config.name}" created successfully!')
            return redirect('core:smtp_configuration_list')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error creating configuration: {str(e)}')
    
    # Predefined configurations
    predefined_configs = {
        'gmail': {
            'name': 'Gmail',
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'help_text': 'Use your Gmail address and an App Password (not your regular password)'
        },
        'outlook': {
            'name': 'Outlook/Hotmail',
            'host': 'smtp-mail.outlook.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'help_text': 'Use your Outlook/Hotmail email address and password'
        },
        'yahoo': {
            'name': 'Yahoo Mail',
            'host': 'smtp.mail.yahoo.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'help_text': 'Use your Yahoo email address and an App Password'
        },
        'custom': {
            'name': 'Custom SMTP',
            'host': '',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'help_text': 'Enter your custom SMTP server details'
        }
    }
    
    context = {
        'page_title': 'Create SMTP Configuration',
        'predefined_configs': predefined_configs
    }
    
    return render(request, 'smtp_configuration_form.html', context)

@user_passes_test(is_admin)
def smtp_configuration_edit(request, config_id):
    """Edit existing SMTP configuration"""
    config = get_object_or_404(SMTPConfig, id=config_id)
    
    if request.method == 'POST':
        try:
            config.name = request.POST.get('name')
            config.host = request.POST.get('host')
            config.port = int(request.POST.get('port', 587))
            config.use_tls = request.POST.get('use_tls') == 'on'
            config.use_ssl = request.POST.get('use_ssl') == 'on'
            config.username = request.POST.get('username')
            config.password = request.POST.get('password')
            config.from_email = request.POST.get('from_email')
            config.from_name = request.POST.get('from_name', '')
            config.is_active = request.POST.get('is_active') == 'on'
            
            config.full_clean()
            config.save()
            
            # Clear SMTP cache to ensure updated settings are loaded
            from .smtp_settings import clear_smtp_cache
            clear_smtp_cache()
            
            messages.success(request, f'SMTP configuration "{config.name}" updated successfully!')
            return redirect('core:smtp_configuration_list')
            
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
    
    return render(request, 'smtp_configuration_form.html', context)

@user_passes_test(is_admin)
@require_POST
def smtp_configuration_test(request, config_id):
    """Test SMTP configuration"""
    config = get_object_or_404(SMTPConfig, id=config_id)
    
    try:
        # Get recipient email from request
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            recipient_email = data.get('recipient_email', config.username)
        else:
            recipient_email = request.POST.get('recipient_email', config.username)
        
        success, message = config.test_connection(recipient_email)
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
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
            return redirect('core:smtp_configuration_list')
            
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
            return redirect('core:smtp_configuration_list')

@user_passes_test(is_admin)
@require_POST
def smtp_configuration_delete(request, config_id):
    """Delete SMTP configuration"""
    config = get_object_or_404(SMTPConfig, id=config_id)
    config_name = config.name
    
    try:
        config.delete()
        messages.success(request, f'SMTP configuration "{config_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting configuration: {str(e)}')
    
    return redirect('core:smtp_configuration_list')

@user_passes_test(is_admin)
@require_POST
def smtp_configuration_activate(request, config_id):
    """Activate SMTP configuration"""
    config = get_object_or_404(SMTPConfig, id=config_id)
    
    try:
        # Deactivate all other configurations
        SMTPConfig.objects.filter(is_active=True).update(is_active=False)
        
        # Activate this configuration
        SMTPConfig.objects.filter(pk=config.pk).update(is_active=True)
        
        # Clear SMTP cache to ensure new active settings are loaded
        from .smtp_settings import clear_smtp_cache
        clear_smtp_cache()
        
        messages.success(request, f'SMTP configuration "{config.name}" activated successfully!')
    except Exception as e:
        messages.error(request, f'Error activating configuration: {str(e)}')
    
    return redirect('core:smtp_configuration_list')

@user_passes_test(is_admin)
def smtp_quick_setup(request):
    """Quick setup wizard for common email providers"""
    if request.method == 'POST':
        provider = request.POST.get('provider')
        email = request.POST.get('from_email') or request.POST.get('email')  # Support both field names
        password = request.POST.get('password')
        from_name = request.POST.get('from_name', 'NORSU Alumni')
        
        # Provider configurations
        provider_configs = {
            'gmail': {
                'name': 'Gmail',
                'host': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            'outlook': {
                'name': 'Outlook',
                'host': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True,
                'use_ssl': False
            },
            'yahoo': {
                'name': 'Yahoo',
                'host': 'smtp.mail.yahoo.com',
                'port': 587,
                'use_tls': True,
                'use_ssl': False
            }
        }
        
        if provider in provider_configs:
            try:
                config_data = provider_configs[provider]
                # Get username from form or use email as username
                username = request.POST.get('username') or email
                
                # Debug logging
                logger.info(f"Quick setup form data - Provider: {provider}, Email: {email}, Username: {username}")
                
                config = SMTPConfig(
                    name=config_data['name'],
                    host=config_data['host'],
                    port=config_data['port'],
                    use_tls=config_data['use_tls'],
                    use_ssl=config_data['use_ssl'],
                    username=username,
                    password=password,
                    from_email=email,
                    from_name=from_name,
                    is_active=True
                )
                
                config.full_clean()
                # Save the configuration directly to avoid datetime field issues
                config.save()
                
                # Clear SMTP cache to ensure new settings are loaded
                from .smtp_settings import clear_smtp_cache
                clear_smtp_cache()
                
                # Test the configuration
                success, message = config.test_connection()
                
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    if success:
                        return JsonResponse({
                            'success': True,
                            'message': f'SMTP configuration created and tested successfully! {message}',
                            'config_name': config.name,
                            'is_active': config.is_active
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': f'Configuration created but test failed: {message}',
                            'details': 'Please check your email credentials and try again.'
                        })
                else:
                    # Regular form submission
                    if success:
                        messages.success(request, f'SMTP configuration created and tested successfully! {message}')
                    else:
                        messages.warning(request, f'Configuration created but test failed: {message}')
                    
                    return redirect('core:smtp_configuration_list')
                
            except ValidationError as e:
                error_messages = []
                for field, errors in e.message_dict.items():
                    for error in errors:
                        error_messages.append(f'{field}: {error}')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'message': 'Validation failed',
                        'details': '; '.join(error_messages)
                    })
                else:
                    for error in error_messages:
                        messages.error(request, error)
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'message': 'Error creating configuration',
                        'details': str(e)
                    })
                else:
                    messages.error(request, f'Error creating configuration: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid provider selected',
                    'details': 'Please select a valid email provider.'
                })
            else:
                messages.error(request, 'Invalid provider selected')
    
    context = {
        'page_title': 'Quick SMTP Setup',
        'providers': [
            {
                'id': 'gmail',
                'name': 'Gmail',
                'description': 'Use your Gmail account with App Password',
                'help': 'Enable 2FA and create an App Password in your Google Account settings'
            },
            {
                'id': 'outlook',
                'name': 'Outlook/Hotmail',
                'description': 'Use your Outlook or Hotmail account',
                'help': 'Use your regular email password'
            },
            {
                'id': 'yahoo',
                'name': 'Yahoo Mail',
                'description': 'Use your Yahoo Mail account with App Password',
                'help': 'Enable 2FA and create an App Password in your Yahoo Account settings'
            }
        ]
    }
    
    return render(request, 'smtp_quick_setup.html', context)
