"""
Views for the setup app.
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from .forms import SuperuserForm
from .models import SetupState
from .utils import is_setup_complete
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SetupWelcomeView(TemplateView):
    """Welcome page for setup process."""
    template_name = 'setup/welcome.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['setup_complete'] = is_setup_complete()
        return context


class SuperuserSetupView(FormView):
    """Superuser creation setup."""
    template_name = 'setup/superuser_setup.html'
    form_class = SuperuserForm
    success_url = reverse_lazy('setup:complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['setup_complete'] = is_setup_complete()
        return context
    
    def form_valid(self, form):
        try:
            # Create the superuser
            user = User.objects.create_superuser(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )
            
            logger.info(f'Superuser created successfully: {user.username}')
            messages.success(self.request, f'Admin account "{user.username}" created successfully!')
            
            # Store superuser info in session for completion page
            self.request.session['created_superuser'] = {
                'username': user.username,
                'email': user.email,
                'created_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f'Failed to create superuser: {e}')
            messages.error(self.request, f'Failed to create admin account: {str(e)}')
            return self.form_invalid(form)
        
        return super().form_valid(form)


class SetupCompleteView(TemplateView):
    """Setup completion page."""
    template_name = 'setup/complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get superuser info from session
        superuser_info = self.request.session.get('created_superuser', {})
        context['superuser_info'] = superuser_info
        
        # Mark setup as complete
        try:
            setup_state, created = SetupState.objects.get_or_create(
                id=1,
                defaults={
                    'is_complete': True,
                    'completed_at': timezone.now(),
                    'setup_data': {
                        'superuser_created': True,
                        'superuser_info': superuser_info
                    }
                }
            )
            if not created:
                setup_state.is_complete = True
                setup_state.completed_at = timezone.now()
                setup_state.setup_data = {
                    'superuser_created': True,
                    'superuser_info': superuser_info
                }
                setup_state.save()
            
            logger.info('Setup marked as complete')
            
        except Exception as e:
            logger.error(f'Failed to mark setup as complete: {e}')
        
        # Clear session data
        if 'created_superuser' in self.request.session:
            del self.request.session['created_superuser']
        
        return context