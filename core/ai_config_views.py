"""
AI Configuration Admin Views
Manage AI API keys (Google Gemini, OpenAI) from the custom admin dashboard.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .models.ai_config import AIConfig
from .ai_config_utils import clear_ai_config_cache
import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_admin)
def ai_configuration_list(request):
    """List all AI configurations."""
    configs = AIConfig.objects.all()
    active_config = AIConfig.get_active_config()

    context = {
        'configs': configs,
        'active_config': active_config,
        'page_title': 'AI Configuration',
        'provider_choices': AIConfig.PROVIDER_CHOICES,
    }
    return render(request, 'ai_configuration.html', context)


@user_passes_test(is_admin)
def ai_configuration_create(request):
    """Create a new AI configuration."""
    if request.method == 'POST':
        try:
            config = AIConfig(
                name=request.POST.get('name', '').strip(),
                provider=request.POST.get('provider', 'gemini'),
                api_key=request.POST.get('api_key', '').strip(),
                model_name=request.POST.get('model_name', 'gemini-2.0-flash').strip(),
                is_active=request.POST.get('is_active') == 'on',
                enabled=request.POST.get('enabled', 'on') == 'on',
            )
            config.full_clean()
            config.save()
            clear_ai_config_cache()
            messages.success(request, f'AI configuration "{config.name}" created successfully!')
            return redirect('core:ai_configuration_list')

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error creating configuration: {str(e)}')
            logger.error(f"Error creating AI config: {e}", exc_info=True)

    context = {
        'page_title': 'Add AI Configuration',
        'provider_choices': AIConfig.PROVIDER_CHOICES,
        'model_suggestions': {
            'gemini': ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro'],
            'openai': ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
        },
    }
    return render(request, 'ai_configuration_form.html', context)


@user_passes_test(is_admin)
def ai_configuration_edit(request, config_id):
    """Edit an existing AI configuration."""
    config = get_object_or_404(AIConfig, id=config_id)

    if request.method == 'POST':
        try:
            config.name = request.POST.get('name', '').strip()
            config.provider = request.POST.get('provider', 'gemini')
            # Only update API key if a new one was provided
            new_key = request.POST.get('api_key', '').strip()
            if new_key:
                config.api_key = new_key
            config.model_name = request.POST.get('model_name', 'gemini-2.0-flash').strip()
            config.is_active = request.POST.get('is_active') == 'on'
            config.enabled = request.POST.get('enabled', 'on') == 'on'

            config.full_clean()
            config.save()
            clear_ai_config_cache()
            messages.success(request, f'AI configuration "{config.name}" updated successfully!')
            return redirect('core:ai_configuration_list')

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error updating configuration: {str(e)}')
            logger.error(f"Error updating AI config {config_id}: {e}", exc_info=True)

    context = {
        'config': config,
        'page_title': f'Edit AI Configuration: {config.name}',
        'provider_choices': AIConfig.PROVIDER_CHOICES,
        'model_suggestions': {
            'gemini': ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro'],
            'openai': ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
        },
    }
    return render(request, 'ai_configuration_form.html', context)


@user_passes_test(is_admin)
@require_POST
def ai_configuration_test(request, config_id):
    """Test an AI configuration by making a real API call."""
    config = get_object_or_404(AIConfig, id=config_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        success, message = config.test_configuration()

        if is_ajax:
            return JsonResponse({'success': success, 'message': message})

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

    except Exception as e:
        msg = f'Test failed: {str(e)}'
        logger.error(msg, exc_info=True)
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)

    return redirect('core:ai_configuration_list')


@user_passes_test(is_admin)
@require_POST
def ai_configuration_activate(request, config_id):
    """Activate an AI configuration (deactivates all others)."""
    config = get_object_or_404(AIConfig, id=config_id)
    try:
        AIConfig.objects.filter(is_active=True).update(is_active=False)
        AIConfig.objects.filter(pk=config.pk).update(is_active=True)
        clear_ai_config_cache()
        messages.success(request, f'AI configuration "{config.name}" activated successfully!')
    except Exception as e:
        messages.error(request, f'Error activating configuration: {str(e)}')
    return redirect('core:ai_configuration_list')


@user_passes_test(is_admin)
@require_POST
def ai_configuration_toggle_enabled(request, config_id):
    """Toggle the enabled status of an AI configuration."""
    config = get_object_or_404(AIConfig, id=config_id)
    try:
        config.enabled = not config.enabled
        config.save()
        clear_ai_config_cache()
        status = "enabled" if config.enabled else "disabled"
        messages.success(request, f'AI configuration "{config.name}" {status}.')
    except Exception as e:
        messages.error(request, f'Error toggling status: {str(e)}')
    return redirect('core:ai_configuration_list')


@user_passes_test(is_admin)
@require_POST
def ai_configuration_delete(request, config_id):
    """Delete an AI configuration."""
    config = get_object_or_404(AIConfig, id=config_id)
    config_name = config.name
    try:
        config.delete()
        clear_ai_config_cache()
        messages.success(request, f'AI configuration "{config_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting configuration: {str(e)}')
    return redirect('core:ai_configuration_list')

