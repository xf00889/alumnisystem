#!/usr/bin/env python
"""
Temporary settings override to bypass django-allauth for admin access.
This creates a minimal Django configuration that allows direct admin login.
"""

import os
import django
from django.conf import settings

def create_temp_admin_urls():
    """
    Create a temporary URL configuration that prioritizes Django admin
    """
    print("=== Creating Temporary Admin URL Configuration ===\n")
    
    # Create a temporary urls.py content that puts admin first
    temp_urls_content = '''
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Custom admin login view that bypasses allauth
class DirectAdminLoginView(auth_views.LoginView):
    template_name = 'admin/login.html'
    
    def get_success_url(self):
        return '/admin/'

urlpatterns = [
    # Put admin URLs FIRST to ensure they take priority
    path('admin/', admin.site.urls),
    
    # Add a direct admin login that bypasses allauth
    path('direct-admin-login/', DirectAdminLoginView.as_view(), name='direct_admin_login'),
    
    # Core app URLs
    path('', include('core.urls', namespace='core')),
    
    # Django-allauth URLs (these come AFTER admin)
    path('accounts/', include('allauth.urls')),
    
    # Other app URLs
    path('profile/', include('accounts.urls', namespace='accounts')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('announcements/', include('announcements.urls', namespace='announcements')),
    path('alumni-groups/', include('alumni_groups.urls', namespace='alumni_groups')),
    path('alumni-directory/', include('alumni_directory.urls', namespace='alumni_directory')),
    path('events/', include('events.urls', namespace='events')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('location/', include('location_tracking.urls', namespace='location_tracking')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('mentorship/', include('mentorship.urls', namespace='mentorship')),
    path('api/skills/', include('accounts.urls', namespace='skills')),
    path('surveys/', include('surveys.urls', namespace='surveys')),
    path('donations/', include('donations.urls', namespace='donations')),
    path('connections/', include('connections.urls', namespace='connections')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler500 = 'core.view_handlers.error_handlers.handler500'
'''
    
    # Write the temporary URLs file
    temp_urls_path = 'norsu_alumni/temp_urls.py'
    with open(temp_urls_path, 'w') as f:
        f.write(temp_urls_content)
    
    print(f"✓ Created temporary URLs file: {temp_urls_path}")
    
    return temp_urls_path

def create_minimal_settings_override():
    """
    Create a minimal settings override for admin-only access
    """
    print("\n=== Creating Minimal Settings Override ===\n")
    
    minimal_settings = '''
# Minimal settings override for admin access
# This temporarily disables django-allauth to allow direct admin login

# Override authentication backends to use only Django's default
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Remove allauth backend
]

# Override login URLs to use Django admin
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# Disable allauth account settings
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Ensure admin site is accessible
ADMIN_ENABLED = True

# Override ROOT_URLCONF to use our temporary URLs
# ROOT_URLCONF = 'norsu_alumni.temp_urls'
'''
    
    settings_override_path = 'norsu_alumni/admin_settings_override.py'
    with open(settings_override_path, 'w') as f:
        f.write(minimal_settings)
    
    print(f"✓ Created settings override file: {settings_override_path}")
    
    return settings_override_path

def create_admin_only_manage_command():
    """
    Create a management command to run Django with admin-only settings
    """
    print("\n=== Creating Admin-Only Management Command ===\n")
    
    # Create management command directory if it doesn't exist
    os.makedirs('core/management/commands', exist_ok=True)
    
    admin_command = '''
from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line
import os
import sys

class Command(BaseCommand):
    help = 'Run Django with admin-only settings (bypasses allauth)'
    
    def add_arguments(self, parser):
        parser.add_argument('--port', type=int, default=8000, help='Port to run on')
        parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    
    def handle(self, *args, **options):
        # Override settings to disable allauth
        os.environ['DJANGO_ADMIN_ONLY'] = 'True'
        
        # Import and modify settings
        from django.conf import settings
        
        # Override authentication backends
        settings.AUTHENTICATION_BACKENDS = [
            'django.contrib.auth.backends.ModelBackend',
        ]
        
        # Override login URLs
        settings.LOGIN_URL = '/admin/login/'
        settings.LOGIN_REDIRECT_URL = '/admin/'
        
        self.stdout.write(
            self.style.SUCCESS('Starting Django with admin-only settings...')
        )
        self.stdout.write(f'Admin will be available at: http://{options["host"]}:{options["port"]}/admin/')
        self.stdout.write('Login with: admin / 123')
        
        # Start the development server
        execute_from_command_line([
            'manage.py', 'runserver', 
            f'{options["host"]}:{options["port"]}'
        ])
'''
    
    command_path = 'core/management/commands/run_admin_only.py'
    with open(command_path, 'w') as f:
        f.write(admin_command)
    
    print(f"✓ Created admin-only command: {command_path}")
    print("  Usage: python manage.py run_admin_only --port 8000")
    
    return command_path

def provide_implementation_instructions():
    """
    Provide step-by-step instructions for implementing the fix
    """
    print("\n=== IMPLEMENTATION INSTRUCTIONS ===\n")
    
    print("OPTION 1: Quick Fix (Recommended)")
    print("1. Run: python create_direct_admin_login.py")
    print("2. Go to: https://your-app.onrender.com/admin/")
    print("3. Login with: admin / 123")
    print("4. This should work immediately")
    
    print("\nOPTION 2: Temporary URL Override")
    print("1. Replace norsu_alumni/urls.py with the temp_urls.py content")
    print("2. Commit and push the changes")
    print("3. Wait for deployment")
    print("4. Try admin login again")
    
    print("\nOPTION 3: Settings Override (If other options fail)")
    print("1. Add the admin_settings_override.py content to settings.py")
    print("2. Temporarily comment out allauth from INSTALLED_APPS")
    print("3. Commit and push")
    print("4. Try admin login")
    print("5. Revert changes after confirming admin works")
    
    print("\nDEBUGGING STEPS:")
    print("1. Check Render logs during login attempt")
    print("2. Run: python bypass_allauth_admin.py (on Render shell)")
    print("3. Verify database connectivity")
    print("4. Check for CSRF token issues")
    
    print("\nROOT CAUSE ANALYSIS:")
    print("The issue is likely that django-allauth is intercepting")
    print("admin login attempts and redirecting them through its")
    print("own authentication system, which may not be properly")
    print("configured for superuser access in production.")

if __name__ == '__main__':
    create_temp_admin_urls()
    create_minimal_settings_override()
    create_admin_only_manage_command()
    provide_implementation_instructions()