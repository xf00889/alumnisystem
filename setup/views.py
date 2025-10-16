"""
Views for the setup app.
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
from django.core.management import call_command
from django.utils import timezone
from .forms import InitialSetupForm, EmailConfigForm, SuperuserForm
from .models import SetupState
from .utils import get_setup_progress, is_setup_complete
import logging
import json

logger = logging.getLogger(__name__)
User = get_user_model()


class SetupWelcomeView(TemplateView):
    """Welcome page for setup process."""
    template_name = 'setup/welcome.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = get_setup_progress()
        return context


class BasicConfigView(FormView):
    """Basic configuration setup."""
    template_name = 'setup/basic_config.html'
    form_class = InitialSetupForm
    success_url = reverse_lazy('setup:email_config')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = get_setup_progress()
        return context
    
    def form_valid(self, form):
        # Store basic configuration in session (this should work even without database)
        try:
            self.request.session['setup_data'] = {
                'basic_config': form.cleaned_data
            }
            self.request.session.save()
        except Exception as e:
            logger.error(f'Failed to save session data: {e}')
            # If session fails, we'll store in a temporary way
            # This is a fallback for when database is completely unavailable
        
        # Also save to database for persistence (if database is ready)
        try:
            from .models import SiteConfiguration
            SiteConfiguration.set_setting('site_name', form.cleaned_data['site_name'], 'Site name')
            SiteConfiguration.set_setting('site_description', form.cleaned_data['site_description'], 'Site description')
            SiteConfiguration.set_setting('admin_email', form.cleaned_data['admin_email'], 'Admin email')
            SiteConfiguration.set_setting('timezone', form.cleaned_data['timezone'], 'Site timezone')
            logger.info('Configuration saved to database successfully')
        except Exception as e:
            logger.warning(f'Database not ready, storing in session only: {e}')
            # Continue with session storage only
        
        messages.success(self.request, 'Basic configuration saved successfully!')
        return super().form_valid(form)


class EmailConfigView(FormView):
    """Email configuration setup."""
    template_name = 'setup/email_config.html'
    form_class = EmailConfigForm
    success_url = reverse_lazy('setup:database_setup')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = get_setup_progress()
        return context
    
    def form_valid(self, form):
        # Store email configuration in session
        setup_data = self.request.session.get('setup_data', {})
        setup_data['email_config'] = form.cleaned_data
        self.request.session['setup_data'] = setup_data
        
        # Also save to database for persistence
        try:
            from .models import EmailConfiguration
            email_config, created = EmailConfiguration.objects.get_or_create(
                name='Default Email Configuration',
                defaults={
                    'backend': form.cleaned_data['email_backend'],
                    'host': form.cleaned_data.get('email_host', ''),
                    'port': form.cleaned_data.get('email_port', 587),
                    'use_tls': form.cleaned_data.get('email_use_tls', True),
                    'username': form.cleaned_data.get('email_host_user', ''),
                    'password': form.cleaned_data.get('email_host_password', ''),
                    'from_email': form.cleaned_data.get('default_from_email', ''),
                }
            )
            if not created:
                email_config.backend = form.cleaned_data['email_backend']
                email_config.host = form.cleaned_data.get('email_host', '')
                email_config.port = form.cleaned_data.get('email_port', 587)
                email_config.use_tls = form.cleaned_data.get('email_use_tls', True)
                email_config.username = form.cleaned_data.get('email_host_user', '')
                email_config.password = form.cleaned_data.get('email_host_password', '')
                email_config.from_email = form.cleaned_data.get('default_from_email', '')
                email_config.save()
        except Exception as e:
            logger.error(f'Failed to save email configuration: {e}')
        
        messages.success(self.request, 'Email configuration saved successfully!')
        return super().form_valid(form)


class DatabaseSetupView(TemplateView):
    """Database setup and migration step."""
    template_name = 'setup/database_setup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = get_setup_progress()
        context['database_status'] = self._check_database_status()
        context['migration_status'] = self._check_migration_status()
        return context
    
    def post(self, request):
        """Run migrations manually."""
        try:
            from django.core.management import call_command
            logger.info("Starting manual migration process...")
            call_command('migrate', verbosity=2, interactive=False)
            
            # Verify tables were created
            if self._check_migration_status()['all_ready']:
                messages.success(request, '✅ Migrations completed successfully! Database is now ready.')
                logger.info("Manual migrations completed successfully")
                return redirect('setup:superuser_setup')
            else:
                messages.warning(request, '⚠️ Migrations ran but some tables may be missing. Please check the logs.')
                logger.warning("Migrations completed but tables verification failed")
            
        except Exception as e:
            error_msg = f'❌ Migration failed: {str(e)}'
            messages.error(request, error_msg)
            logger.error(f"Manual migration failed: {e}")
        
        return redirect('setup:database_setup')
    
    def _check_database_status(self):
        """Check if database is accessible."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return {
                    'accessible': True,
                    'message': '✅ Database connection successful'
                }
        except Exception as e:
            return {
                'accessible': False,
                'message': f'❌ Database connection failed: {str(e)}'
            }
    
    def _check_migration_status(self):
        """Check if critical tables exist."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Check django_session table
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'django_session'
                        );
                    """)
                    django_session_exists = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'auth_user'
                        );
                    """)
                    auth_user_exists = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'setup_siteconfiguration'
                        );
                    """)
                    setup_tables_exist = cursor.fetchone()[0]
                    
                elif connection.vendor == 'mysql':
                    cursor.execute("SHOW TABLES LIKE 'django_session'")
                    django_session_exists = cursor.fetchone() is not None
                    
                    cursor.execute("SHOW TABLES LIKE 'auth_user'")
                    auth_user_exists = cursor.fetchone() is not None
                    
                    cursor.execute("SHOW TABLES LIKE 'setup_siteconfiguration'")
                    setup_tables_exist = cursor.fetchone() is not None
                else:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='django_session'
                    """)
                    django_session_exists = cursor.fetchone() is not None
                    
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='auth_user'
                    """)
                    auth_user_exists = cursor.fetchone() is not None
                    
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='setup_siteconfiguration'
                    """)
                    setup_tables_exist = cursor.fetchone() is not None
                
                return {
                    'django_session_exists': django_session_exists,
                    'auth_user_exists': auth_user_exists,
                    'setup_tables_exist': setup_tables_exist,
                    'all_ready': django_session_exists and auth_user_exists and setup_tables_exist
                }
                
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return {
                'django_session_exists': False,
                'auth_user_exists': False,
                'setup_tables_exist': False,
                'all_ready': False,
                'error': str(e)
            }


class SuperuserSetupView(FormView):
    """Superuser creation setup."""
    template_name = 'setup/superuser_setup.html'
    form_class = SuperuserForm
    success_url = reverse_lazy('setup:complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = get_setup_progress()
        return context
    
    def form_valid(self, form):
        try:
            # Create superuser (database should be ready at this point)
            user = User.objects.create_superuser(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )
            
            # Store superuser info in session
            setup_data = self.request.session.get('setup_data', {})
            setup_data['superuser'] = {
                'username': user.username,
                'email': user.email,
                'created': True
            }
            self.request.session['setup_data'] = setup_data
            
            messages.success(self.request, f'Superuser "{user.username}" created successfully!')
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f'Failed to create superuser: {e}')
            messages.error(self.request, f'Failed to create superuser: {e}')
            return self.form_invalid(form)


class SetupCompleteView(TemplateView):
    """Setup completion confirmation."""
    template_name = 'setup/complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = get_setup_progress()
        
        # Get setup data from session
        setup_data = self.request.session.get('setup_data', {})
        context['setup_data'] = setup_data
        
        # Complete the setup process
        self.complete_setup(setup_data)
        
        return context
    
    def complete_setup(self, setup_data):
        """Complete the setup process."""
        try:
            # Get or create setup state
            setup_state = SetupState.get_setup_state()
            
            # Prepare final setup data
            final_setup_data = {
                'basic_config': setup_data.get('basic_config', {}),
                'email_config': setup_data.get('email_config', {}),
                'superuser': setup_data.get('superuser', {}),
                'completion_timestamp': timezone.now().isoformat(),
                'completed_by': 'setup_wizard'
            }
            
            # Superuser should already be created at this point
            superuser_data = setup_data.get('superuser', {})
            if superuser_data.get('created', False):
                logger.info(f'Superuser "{superuser_data.get("username", "unknown")}" was created successfully')
            else:
                logger.warning('No superuser was created during setup')
            
            # Mark setup as complete
            setup_state.mark_complete(final_setup_data)
            
            # Clear session data
            if 'setup_data' in self.request.session:
                del self.request.session['setup_data']
            
            logger.info('Setup completed successfully')
            
        except Exception as e:
            logger.error(f'Failed to complete setup: {e}')
            messages.error(self.request, f'Setup completion failed: {e}')


class SetupProgressView(TemplateView):
    """API view to get setup progress."""
    template_name = 'setup/progress.html'
    
    def get(self, request, *args, **kwargs):
        from .utils import get_setup_progress
        progress = get_setup_progress()
        return JsonResponse(progress)


class TestEmailConfigView(TemplateView):
    """API view to test email configuration."""
    
    def post(self, request, *args, **kwargs):
        try:
            # Test email configuration
            send_mail(
                'Test Email from Setup',
                'This is a test email to verify your email configuration.',
                settings.DEFAULT_FROM_EMAIL,
                [request.POST.get('test_email', '')],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': 'Email sent successfully!'})
        except Exception as e:
            logger.error(f"Email test failed: {e}")
            return JsonResponse({'success': False, 'message': str(e)})


class CheckDatabaseView(TemplateView):
    """API view to check database connection."""
    
    def get(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            return JsonResponse({'success': True, 'message': 'Database connection successful!'})
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return JsonResponse({'success': False, 'message': str(e)})
