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
import json

logger = logging.getLogger(__name__)

def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(is_admin)
def smtp_configuration_list(request):
    """List all email configurations (SMTP and Brevo)"""
    smtp_configs = SMTPConfig.objects.all()
    
    # Import BrevoConfig here to avoid circular imports
    from .models.brevo_config import BrevoConfig
    brevo_configs = BrevoConfig.objects.all()
    
    # Get active configurations
    active_smtp = SMTPConfig.objects.filter(is_active=True).first()
    active_brevo = BrevoConfig.objects.filter(is_active=True).first()
    
    context = {
        'smtp_configs': smtp_configs,
        'brevo_configs': brevo_configs,
        'page_title': 'Email Configuration',
        'active_smtp': active_smtp,
        'active_brevo': active_brevo
    }
    
    return render(request, 'smtp_configuration_list.html', context)

from .forms.smtp_configuration import SMTPConfigurationForm


def _smtp_form_context(request, form, config=None):
    """Retain submitted values on validation errors without exposing credentials."""
    data = {}
    fields = ('name', 'host', 'port', 'username', 'from_email', 'from_name')
    for field in fields:
        data[field] = request.POST.get(field, '') if request.method == 'POST' else (getattr(config, field, '') if config else '')
    if request.method == 'GET' and not config:
        data.update({'port': 587, 'from_name': 'NORSU Alumni'})
    return {
        'config': config,
        'form_data': data,
        'use_tls_checked': (request.POST.get('use_tls') == 'on' if request.method == 'POST' else (config.use_tls if config else True)),
        'use_ssl_checked': (request.POST.get('use_ssl') == 'on' if request.method == 'POST' else (config.use_ssl if config else False)),
        'is_active_checked': (request.POST.get('is_active') == 'on' if request.method == 'POST' else (config.is_active if config else False)),
        'form_errors': form.errors if request.method == 'POST' else None,
        'show_configuration_form': (request.method == 'POST' or bool(config)),
    }


def _save_smtp_form(request, form, config=None):
    if not form.is_valid():
        return None, form

    candidate = form.save(commit=False)
    if config is None:
        candidate.is_verified = False
        candidate.is_active = False
    else:
        sensitive_fields = {'host', 'port', 'use_tls', 'use_ssl', 'username', 'password', 'from_email'}
        if any(name in form.changed_data for name in sensitive_fields):
            candidate.is_verified = False
            candidate.is_active = False
            candidate.test_result = 'Configuration changed; re-test before activation.'
        elif candidate.is_active and not candidate.is_verified:
            candidate.is_active = False
    candidate.full_clean()
    candidate.save()
    from .smtp_settings import clear_smtp_cache
    clear_smtp_cache()
    return candidate, form


@user_passes_test(is_admin)
@require_http_methods(['GET', 'POST'])
def smtp_configuration_create(request):
    if request.method == 'POST':
        form = SMTPConfigurationForm(request.POST)
        try:
            config, form = _save_smtp_form(request, form)
            if config is not None:
                messages.success(request, 'SMTP configuration saved. Use Test, then Activate after verification.')
                return redirect('core:smtp_configuration_list')
        except ValidationError as exc:
            form.add_error(None, exc)
        except Exception:
            logger.exception('SMTP configuration create failed')
            form.add_error(None, 'Unable to save the configuration. Check the server logs.')
    else:
        form = SMTPConfigurationForm()
    context = _smtp_form_context(request, form)
    context['page_title'] = 'Create SMTP Configuration'
    return render(request, 'smtp_configuration_form.html', context)


@user_passes_test(is_admin)
@require_http_methods(['GET', 'POST'])
def smtp_configuration_edit(request, config_id):
    config = get_object_or_404(SMTPConfig, pk=config_id)
    if request.method == 'POST':
        form = SMTPConfigurationForm(request.POST, instance=config)
        try:
            saved, form = _save_smtp_form(request, form, config)
            if saved is not None:
                messages.success(request, 'SMTP configuration updated. Re-test before activation if connection settings changed.')
                return redirect('core:smtp_configuration_list')
        except ValidationError as exc:
            form.add_error(None, exc)
        except Exception:
            logger.exception('SMTP configuration edit failed: id=%s', config_id)
            form.add_error(None, 'Unable to save the configuration. Check the server logs.')
    else:
        form = SMTPConfigurationForm(instance=config)
    context = _smtp_form_context(request, form, config)
    context['page_title'] = 'Edit SMTP Configuration'
    return render(request, 'smtp_configuration_form.html', context)


@user_passes_test(is_admin)
@require_POST
def smtp_configuration_test(request, config_id):
    """Test SMTP configuration"""
    try:
        config = get_object_or_404(SMTPConfig, id=config_id)
        
        # Get recipient email from request
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            recipient_email = data.get('recipient_email', config.username)
            send_test_email = data.get('send_test_email', True)  # Default to sending email
        else:
            recipient_email = request.POST.get('recipient_email', config.username)
            send_test_email = request.POST.get('send_test_email', 'on') == 'on'
        
        success, message = config.test_connection(recipient_email, send_test_email)
        
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
        logger.error(f"SMTP test error: {error_message}")
        
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
    try:
        config = get_object_or_404(SMTPConfig, id=config_id)
        config_name = config.name
        
        config.delete()
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'SMTP configuration "{config_name}" deleted successfully!'
            })
        else:
            messages.success(request, f'SMTP configuration "{config_name}" deleted successfully!')
            return redirect('core:smtp_configuration_list')
            
    except Exception as e:
        error_message = f'Error deleting configuration: {str(e)}'
        logger.error(f"SMTP delete error: {error_message}")
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'message': error_message
            })
        else:
            messages.error(request, error_message)
            return redirect('core:smtp_configuration_list')

def _select_email_provider(provider_type):
    from .models.email_provider import EmailProvider
    provider = EmailProvider.objects.filter(provider_type=provider_type).first()
    if provider is None:
        provider = EmailProvider(provider_type=provider_type, is_active=True)
    else:
        provider.is_active = True
    provider.save()


@user_passes_test(is_admin)
@require_POST
def smtp_configuration_activate(request, config_id):
    config = get_object_or_404(SMTPConfig, pk=config_id)
    if not config.is_verified:
        messages.error(request, 'Test and verify this SMTP configuration before activating it.')
        return redirect('core:smtp_configuration_list')
    from django.db import transaction
    with transaction.atomic():
        SMTPConfig.objects.filter(is_active=True).exclude(pk=config.pk).update(is_active=False)
        SMTPConfig.objects.filter(pk=config.pk).update(is_active=True)
        _select_email_provider('smtp')
    from .smtp_settings import clear_smtp_cache
    clear_smtp_cache()
    messages.success(request, 'SMTP configuration activated as the system email provider.')
    return redirect('core:smtp_configuration_list')


@user_passes_test(is_admin)
@require_http_methods(['GET', 'POST'])
def smtp_quick_setup(request):
    """Quick setup wizard for common email providers"""
    if request.method == 'POST':
        provider = request.POST.get('provider')
        email = request.POST.get('from_email') or request.POST.get('email')  # Support both field names
        password = request.POST.get('password')
        from_name = (request.POST.get('from_name') or 'NORSU Alumni').strip()
        
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
        
        if provider == 'brevo':
            # Handle Brevo configuration
            try:
                api_key = request.POST.get('api_key')
                config_name = request.POST.get('name', 'Brevo Configuration')
                
                if not api_key:
                    raise ValueError('Brevo API key is required')
                
                # Import BrevoConfig here to avoid circular imports
                from .models.brevo_config import BrevoConfig
                
                config = BrevoConfig(
                    name=config_name,
                    api_key=api_key,
                    api_url='https://api.brevo.com/v3/smtp/email',
                    from_email=email,
                    from_name=from_name,
                    is_active=False
                )
                
                config.full_clean()
                config.save()
                
                # Test the configuration
                success, message = config.test_connection()
                if success:
                    from django.db import transaction
                    with transaction.atomic():
                        BrevoConfig.objects.filter(is_active=True).exclude(pk=config.pk).update(is_active=False)
                        BrevoConfig.objects.filter(pk=config.pk).update(is_active=True)
                        _select_email_provider('brevo')
                    from .brevo_email import clear_brevo_cache
                    clear_brevo_cache()
                config.is_active = bool(success)

                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    if success:
                        return JsonResponse({
                            'success': True,
                            'message': f'Brevo configuration created and tested successfully! {message}',
                            'config_name': config.name,
                            'is_active': config.is_active
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': f'Configuration created but test failed: {message}',
                            'details': 'Please check your Brevo API key and try again.'
                        })
                else:
                    # Regular form submission
                    if success:
                        messages.success(request, f'Brevo configuration created and tested successfully! {message}')
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
                        'message': 'Error creating Brevo configuration',
                        'details': str(e)
                    })
                else:
                    messages.error(request, f'Error creating Brevo configuration: {str(e)}')
                
        elif provider in provider_configs or provider == 'custom':
            try:
                from django.db import transaction
                raw_password = (request.POST.get('password') or '').strip()
                if not raw_password:
                    raise ValueError('An SMTP app password is required.')
                config_data = provider_configs.get(provider)
                if provider == 'custom':
                    config_data = {
                        'name': request.POST.get('name', 'Custom SMTP'),
                        'host': (request.POST.get('host') or '').strip(),
                        'port': int(request.POST.get('port') or 587),
                        'use_tls': request.POST.get('encryption', 'tls') == 'tls',
                        'use_ssl': request.POST.get('encryption', 'tls') == 'ssl',
                    }
                email = (email or '').strip()
                username = (request.POST.get('username') or email).strip()
                config = SMTPConfig(
                    name=(request.POST.get('name') or config_data['name']).strip(),
                    host=config_data['host'],
                    port=config_data['port'],
                    use_tls=config_data['use_tls'],
                    use_ssl=config_data['use_ssl'],
                    username=username,
                    password=raw_password,
                    from_email=email,
                    from_name=(from_name or '').strip() or 'NORSU Alumni',
                    is_active=False,
                    is_verified=False,
                )
                config.full_clean()
                config.save()
                from .smtp_settings import clear_smtp_cache
                clear_smtp_cache()

                # Test actual SMTP authentication; unsuccessful tests leave a saved inactive record.
                success, test_message = config.test_connection(send_test_email=False)
                if success:
                    with transaction.atomic():
                        SMTPConfig.objects.filter(pk=config.pk).update(is_verified=True)
                        SMTPConfig.objects.filter(is_active=True).exclude(pk=config.pk).update(is_active=False)
                        SMTPConfig.objects.filter(pk=config.pk).update(is_active=True)
                        _select_email_provider('smtp')
                    clear_smtp_cache()
                result = {
                    'success': success,
                    'saved': True,
                    'verified': success,
                    'message': 'SMTP configuration saved and verified.' if success else 'SMTP configuration saved, but connection verification failed. It was NOT activated.',
                    'details': test_message,
                    'config_name': config.name,
                    'is_active': success,
                }
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(result)
                if success:
                    messages.success(request, result['message'])
                else:
                    messages.warning(request, result['message'])
                return redirect('core:smtp_configuration_list')
            except (ValidationError, ValueError) as exc:
                logger.info('SMTP quick setup validation failed: %s', type(exc).__name__)
                result = {'success': False, 'saved': False, 'message': 'Please correct the SMTP configuration fields.', 'details': str(exc)}
            except Exception:
                logger.exception('SMTP quick setup failed')
                result = {'success': False, 'saved': False, 'message': 'Unable to save SMTP settings. Check server logs.'}
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(result, status=400)
            messages.error(request, result['message'])
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

# Brevo Configuration Admin Views
@user_passes_test(is_admin)
def brevo_configuration_test(request, config_id):
    """Test Brevo configuration"""
    try:
        from .models.brevo_config import BrevoConfig
        config = BrevoConfig.objects.get(id=config_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            recipient_email = data.get('recipient_email')
            send_test_email = data.get('send_test_email', False)
            
            if not recipient_email:
                return JsonResponse({
                    'success': False,
                    'message': 'Recipient email is required'
                })
            
            success, message = config.test_connection(recipient_email, send_test_email)
            
            return JsonResponse({
                'success': success,
                'message': message
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })
        
    except BrevoConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Brevo configuration not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error testing configuration: {str(e)}'
        })

@user_passes_test(is_admin)
def brevo_configuration_activate(request, config_id):
    """Activate Brevo configuration"""
    try:
        from .models.brevo_config import BrevoConfig
        config = BrevoConfig.objects.get(id=config_id)
        
        if request.method == 'POST':
            # Deactivate all other configurations
            BrevoConfig.objects.filter(is_active=True).exclude(id=config_id).update(is_active=False)
            
            # Activate this configuration
            config.is_active = True
            config.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Brevo configuration "{config.name}" activated successfully'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })
        
    except BrevoConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Brevo configuration not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error activating configuration: {str(e)}'
        })

@user_passes_test(is_admin)
def brevo_configuration_edit(request, config_id):
    """Edit existing Brevo configuration"""
    from .models.brevo_config import BrevoConfig
    config = get_object_or_404(BrevoConfig, id=config_id)
    
    if request.method == 'POST':
        try:
            config.name = request.POST.get('name')
            config.api_key = request.POST.get('api_key') or config.api_key
            config.api_url = request.POST.get('api_url', 'https://api.brevo.com/v3/smtp/email')
            config.from_email = request.POST.get('from_email')
            config.from_name = request.POST.get('from_name', '')
            config.is_active = request.POST.get('is_active') == 'on'
            
            config.full_clean()
            config.save()
            
            # Clear Brevo cache to ensure updated settings are loaded
            from .brevo_email import clear_brevo_cache
            clear_brevo_cache()
            
            messages.success(request, f'Brevo configuration "{config.name}" updated successfully!')
            return redirect('core:smtp_configuration_list')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error updating configuration: {str(e)}')
    
    context = {
        'config': config,
        'page_title': f'Edit {config.name}',
        'config_type': 'brevo'
    }
    
    return render(request, 'brevo_configuration_form.html', context)

@user_passes_test(is_admin)
def brevo_configuration_delete(request, config_id):
    """Delete Brevo configuration"""
    try:
        from .models.brevo_config import BrevoConfig
        config = BrevoConfig.objects.get(id=config_id)
        
        if request.method == 'POST':
            config_name = config.name
            config.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Brevo configuration "{config_name}" deleted successfully'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })
        
    except BrevoConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Brevo configuration not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting configuration: {str(e)}'
        })
