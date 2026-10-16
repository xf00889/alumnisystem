"""Deny coordinator-only accounts access to jobs, HR, system and user administration.

Server-side boundary, independent of navigation display. Other roles retain existing rules.
"""
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class CoordinatorAccessMiddleware(MiddlewareMixin):
    FORBIDDEN_ADMIN = ('users/', 'smtp/', 'brevo/', 'recaptcha/', 'sso/', 'ai/', 'seo/', 'system/')
    FORBIDDEN_EXPORT = ('/export/', '/bulk-export/', '/api/dashboard-analytics/', '/api/alumni-by-college/')

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or user.is_staff or user.is_superuser:
            return None
        profile = getattr(user, 'profile', None)
        if not profile or not profile.is_alumni_coordinator:
            return None
        path = request.path_info.lstrip('/')
        if path.startswith('jobs/') or path.startswith('admin-dashboard/users/') or any(path.startswith('admin-dashboard/'+part) for part in self.FORBIDDEN_ADMIN) or request.path_info.startswith(self.FORBIDDEN_EXPORT):
            raise PermissionDenied('Your coordinator account cannot access career or system administration.')
        if path == 'admin-dashboard/':
            return redirect('core:coordinator_dashboard')
        return None
