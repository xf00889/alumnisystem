"""
User Management Views for Admin Dashboard

Provides comprehensive user account management including:
- User listing with search and filtering
- User creation
- User detail viewing
- Role management (AJAX)
- Status toggling (AJAX)
- Bulk operations (AJAX)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from core.mixins import SuperuserRequiredMixin, StaffRequiredMixin
from core.forms.user_management_forms import UserCreationForm, UserSearchForm
from core.services import UserManagementService, RoleAssignmentService, AuditLogService
from core.models.user_management import UserAuditLog, UserStatusChange
from accounts.models import Profile, Mentor

import logging

User = get_user_model()
logger = logging.getLogger('core')


class UserListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    List all users with search and filtering capabilities.
    
    Features:
    - Search by email, first name, or last name
    - Filter by role (alumni, mentor, hr, admin, superuser)
    - Filter by status (active/inactive)
    - Pagination (25 users per page)
    - Role and status counts for UI
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 10.1
    """
    
    model = User
    template_name = 'admin/user_management/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        """
        Build queryset with search, filtering, and sorting applied.
        
        Combines multiple filters using AND logic (Requirement 4.5).
        Supports sorting by name, status, and last_login.
        """
        # Base queryset with related data for efficiency
        queryset = User.objects.select_related('profile').prefetch_related(
            Prefetch('mentor_profile', queryset=Mentor.objects.filter(is_active=True))
        )
        
        # Get filter parameters
        search_query = self.request.GET.get('search', '').strip()
        role_filter = self.request.GET.get('role', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        sort_param = self.request.GET.get('sort', '').strip()
        
        # Apply search filter (Requirement 4.2)
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Apply role filter (Requirement 4.3)
        if role_filter:
            if role_filter == 'superuser':
                queryset = queryset.filter(is_superuser=True)
            elif role_filter == 'admin':
                queryset = queryset.filter(is_staff=True, is_superuser=False)
            elif role_filter == 'hr':
                queryset = queryset.filter(profile__is_hr=True)
            elif role_filter == 'mentor':
                queryset = queryset.filter(mentor_profile__is_active=True)
            elif role_filter == 'alumni':
                # Alumni are users without special roles
                queryset = queryset.filter(
                    is_staff=False,
                    is_superuser=False,
                    profile__is_hr=False
                ).exclude(mentor_profile__is_active=True)
        
        # Apply status filter (Requirement 4.4)
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        # Apply sorting
        if sort_param:
            # Map sort fields to actual database fields
            sort_mapping = {
                'name': 'first_name',
                '-name': '-first_name',
                'status': 'is_active',
                '-status': '-is_active',
                'last_login': 'last_login',
                '-last_login': '-last_login',
            }
            
            # Get the actual field name
            sort_field = sort_mapping.get(sort_param)
            
            if sort_field:
                # Handle null values for last_login
                if 'last_login' in sort_field:
                    # Put null values last
                    from django.db.models import F
                    if sort_field.startswith('-'):
                        queryset = queryset.order_by(F('last_login').desc(nulls_last=True))
                    else:
                        queryset = queryset.order_by(F('last_login').asc(nulls_last=True))
                else:
                    queryset = queryset.order_by(sort_field)
            else:
                # Default sort
                queryset = queryset.order_by('-date_joined')
        else:
            # Default sort by date joined (newest first)
            queryset = queryset.order_by('-date_joined')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add search form and filter counts to context.
        
        Requirements: 4.1, 4.6, 10.1
        """
        context = super().get_context_data(**kwargs)
        
        # Add search form with current values
        context['search_form'] = UserSearchForm(self.request.GET or None)
        
        # Add current filter values for UI state
        context['current_search'] = self.request.GET.get('search', '')
        context['current_role'] = self.request.GET.get('role', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        
        # Add role counts for UI badges
        context['role_counts'] = {
            'total': User.objects.count(),
            'superuser': User.objects.filter(is_superuser=True).count(),
            'admin': User.objects.filter(is_staff=True, is_superuser=False).count(),
            'hr': User.objects.filter(profile__is_hr=True).count(),
            'mentor': User.objects.filter(mentor_profile__is_active=True).count(),
        }
        
        # Add status counts for UI badges
        context['status_counts'] = {
            'active': User.objects.filter(is_active=True).count(),
            'inactive': User.objects.filter(is_active=False).count(),
        }
        
        # Add permission flags for UI
        context['is_superuser'] = self.request.user.is_superuser
        context['can_create_users'] = self.request.user.is_superuser
        context['can_modify_users'] = self.request.user.is_superuser
        
        return context




class UserCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    """
    Create a new user account.
    
    Features:
    - Form validation for email uniqueness and password complexity
    - Calls UserManagementService for transaction-safe creation
    - Sends welcome email with credentials
    - Logs audit trail
    - Success/error messages
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """
    
    model = User
    form_class = UserCreationForm
    template_name = 'admin/user_management/user_create.html'
    success_url = reverse_lazy('core:user_list')
    
    def form_valid(self, form):
        """
        Handle valid form submission.
        
        Calls UserManagementService.create_user() for transaction-safe creation.
        Requirements: 1.3, 1.4, 1.6
        """
        # Extract form data
        email = form.cleaned_data['email']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        password = form.cleaned_data['password']
        send_email = form.cleaned_data.get('send_welcome_email', True)
        
        # Call service to create user
        user, profile, success, error_message = UserManagementService.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            created_by=self.request.user,
            request=self.request,
            send_email=send_email
        )
        
        if success:
            # Success message (Requirement 1.1)
            messages.success(
                self.request,
                f'User account created successfully for {email}. '
                f'{"Welcome email sent." if send_email else "No email sent."}'
            )
            
            logger.info(
                f"User {email} created via admin dashboard by {self.request.user.email}",
                extra={
                    'user_id': user.id,
                    'created_by': self.request.user.email,
                    'action': 'user_created_via_dashboard'
                }
            )
            
            return redirect(self.success_url)
        else:
            # Error message
            messages.error(
                self.request,
                f'Failed to create user: {error_message}'
            )
            
            logger.error(
                f"Failed to create user {email} via admin dashboard: {error_message}",
                extra={
                    'email': email,
                    'created_by': self.request.user.email,
                    'error': error_message,
                    'action': 'user_creation_failed_via_dashboard'
                }
            )
            
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle invalid form submission.
        
        Display error messages for validation failures.
        """
        messages.error(
            self.request,
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add additional context for template"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New User'
        context['submit_button_text'] = 'Create User'
        return context




class UserDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """
    View detailed user information and audit trail.
    
    Features:
    - Display user information and profile data
    - Show current roles with badges
    - Display audit trail (paginated, 20 per page)
    - Show related records count
    - Role management interface (for superusers)
    - Status toggle button (for superusers)
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    model = User
    template_name = 'admin/user_management/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_queryset(self):
        """Optimize query with related data"""
        return User.objects.select_related('profile').prefetch_related(
            'mentor_profile',
            'user_management_audit_logs__performed_by',
            'status_changes__changed_by'
        )
    
    def get_context_data(self, **kwargs):
        """
        Add comprehensive user information to context.
        
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        context = super().get_context_data(**kwargs)
        user_obj = self.object
        
        # Get user roles (Requirement 5.1)
        context['user_roles'] = RoleAssignmentService.get_user_roles(user_obj)
        
        # Add profile information (Requirement 5.1)
        try:
            context['profile'] = user_obj.profile
        except Profile.DoesNotExist:
            context['profile'] = None
        
        # Add mentor profile if exists (Requirement 5.4)
        try:
            context['mentor_profile'] = user_obj.mentor_profile
        except Mentor.DoesNotExist:
            context['mentor_profile'] = None
        
        # Get audit trail with pagination (Requirement 5.2, 5.3, 5.5)
        audit_logs = UserAuditLog.objects.filter(
            user=user_obj
        ).select_related('performed_by').order_by('-timestamp')
        
        # Paginate audit logs (20 per page)
        paginator = Paginator(audit_logs, 20)
        page_number = self.request.GET.get('page', 1)
        context['audit_logs'] = paginator.get_page(page_number)
        
        # Get status change history (Requirement 5.3)
        context['status_changes'] = UserStatusChange.objects.filter(
            user=user_obj
        ).select_related('changed_by').order_by('-timestamp')[:10]
        
        # Get related records count (Requirement 5.4)
        context['related_counts'] = {
            'audit_logs': audit_logs.count(),
            'status_changes': UserStatusChange.objects.filter(user=user_obj).count(),
        }
        
        # Try to get additional related counts if models exist
        try:
            from jobs.models import JobApplication
            context['related_counts']['job_applications'] = JobApplication.objects.filter(
                applicant=user_obj
            ).count()
        except ImportError:
            pass
        
        try:
            from events.models import EventRegistration
            context['related_counts']['event_registrations'] = EventRegistration.objects.filter(
                user=user_obj
            ).count()
        except ImportError:
            pass
        
        try:
            from mentorship.models import MentorshipRequest
            context['related_counts']['mentorship_requests'] = MentorshipRequest.objects.filter(
                Q(mentee=user_obj) | Q(mentor__user=user_obj)
            ).count()
        except ImportError:
            pass
        
        # Add permission flags for UI
        context['is_superuser'] = self.request.user.is_superuser
        context['can_modify_user'] = self.request.user.is_superuser
        context['can_manage_roles'] = self.request.user.is_superuser
        context['can_toggle_status'] = self.request.user.is_superuser
        context['is_viewing_self'] = self.request.user.id == user_obj.id
        
        # Add available roles for role management
        context['available_roles'] = ['hr', 'admin', 'superuser', 'mentor']
        
        return context




@method_decorator(csrf_protect, name='dispatch')
class UserRoleManagementView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """
    Manage user roles via AJAX.
    
    Handles:
    - Role assignment (POST with action=assign)
    - Role removal (POST with action=remove)
    
    Returns JSON responses for AJAX integration.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
    """
    
    def post(self, request, pk):
        """
        Handle role assignment/removal requests.
        
        Expected POST data (JSON):
        - action: 'assign' or 'remove'
        - role: role name ('hr', 'admin', 'superuser', 'mentor')
        - reason: optional reason for the change
        
        Returns JSON:
        {
            "success": true/false,
            "message": "Human-readable message",
            "data": {
                "user_id": int,
                "role": str,
                "action": str,
                "current_roles": [str, ...]
            }
        }
        """
        import json
        
        try:
            # Get user
            user = get_object_or_404(User, pk=pk)
            
            # Parse JSON body if content type is JSON, otherwise fall back to POST
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid JSON data.'
                    }, status=400)
            else:
                data = request.POST
            
            # Get action and role from request data
            action = data.get('action', '').lower()
            role = data.get('role', '').lower()
            
            # Validate action
            if action not in ['assign', 'remove']:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid action: {action}. Must be "assign" or "remove".'
                }, status=400)
            
            # Validate role
            valid_roles = ['hr', 'admin', 'superuser', 'mentor', 'alumni_coordinator']
            if role not in valid_roles:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid role: {role}. Must be one of: {", ".join(valid_roles)}'
                }, status=400)
            
            # Perform action
            if action == 'assign':
                success, error_message = RoleAssignmentService.assign_role(
                    user=user,
                    role_name=role,
                    assigned_by=request.user,
                    request=request,
                    send_email=True
                )
                action_text = 'assigned'
            else:  # remove
                success, error_message = RoleAssignmentService.remove_role(
                    user=user,
                    role_name=role,
                    removed_by=request.user,
                    request=request,
                    send_email=True
                )
                action_text = 'removed'
            
            if success:
                # Get updated roles
                current_roles = RoleAssignmentService.get_user_roles(user)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Role "{role}" {action_text} successfully.',
                    'data': {
                        'user_id': user.id,
                        'role': role,
                        'action': action,
                        'current_roles': current_roles
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': error_message or f'Failed to {action} role.'
                }, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found.'
            }, status=404)
        
        except Exception as e:
            logger.error(
                f"Error in UserRoleManagementView: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': pk,
                    'action': action if 'action' in locals() else None,
                    'role': role if 'role' in locals() else None,
                    'performed_by': request.user.email,
                }
            )
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }, status=500)




@method_decorator(csrf_protect, name='dispatch')
class UserStatusToggleView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """
    Toggle user active status via AJAX.
    
    Handles:
    - Enable user (set is_active=True)
    - Disable user (set is_active=False)
    
    Validates:
    - Cannot disable self
    - Terminates sessions when disabling
    
    Returns JSON responses for AJAX integration.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
    """
    
    def post(self, request, pk):
        """
        Handle status toggle requests.
        
        Expected POST data (JSON):
        - action: 'enable' or 'disable'
        - reason: reason for status change (optional)
        
        Returns JSON:
        {
            "success": true/false,
            "message": "Human-readable message",
            "data": {
                "user_id": int,
                "is_active": bool,
                "status_text": str
            }
        }
        """
        import json
        
        try:
            # Get user
            user = get_object_or_404(User, pk=pk)
            
            # Parse JSON body if content type is JSON, otherwise fall back to POST
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid JSON data.'
                    }, status=400)
            else:
                data = request.POST
            
            # Get action from request - supports both 'action' (enable/disable) and 'is_active' (true/false)
            action = data.get('action', '').lower()
            is_active_str = data.get('is_active', '').lower() if not action else ''
            reason = data.get('reason', '').strip()
            
            # Convert action or is_active to boolean
            if action == 'enable':
                is_active = True
            elif action == 'disable':
                is_active = False
            elif is_active_str == 'true':
                is_active = True
            elif is_active_str == 'false':
                is_active = False
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action. Must be "enable" or "disable".'
                }, status=400)
            
            # Validate reason is provided
            if not reason:
                reason = f"User {'enabled' if is_active else 'disabled'} by {request.user.get_full_name()}"
            
            # Validate cannot disable self (Requirement 3.2)
            if user.id == request.user.id and not is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'You cannot disable your own account.'
                }, status=403)
            
            # Call service to update status
            success, error_message = UserManagementService.update_user_status(
                user=user,
                is_active=is_active,
                reason=reason,
                changed_by=request.user,
                request=request,
                send_email=True
            )
            
            if success:
                status_text = 'Active' if is_active else 'Inactive'
                action_text = 'enabled' if is_active else 'disabled'
                
                return JsonResponse({
                    'success': True,
                    'message': f'User {action_text} successfully.',
                    'data': {
                        'user_id': user.id,
                        'is_active': is_active,
                        'status_text': status_text
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': error_message or 'Failed to update user status.'
                }, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found.'
            }, status=404)
        
        except Exception as e:
            logger.error(
                f"Error in UserStatusToggleView: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': pk,
                    'is_active': is_active_str if 'is_active_str' in locals() else None,
                    'performed_by': request.user.email,
                }
            )
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }, status=500)




@method_decorator(csrf_protect, name='dispatch')
class UserBulkActionView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """
    Perform bulk actions on multiple users via AJAX.
    
    Handles:
    - Bulk enable (set is_active=True for multiple users)
    - Bulk disable (set is_active=False for multiple users)
    
    Features:
    - Process each user independently (Requirement 6.5)
    - Track successes and failures separately
    - Return detailed summary
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    
    def post(self, request):
        """
        Handle bulk action requests.
        
        Expected POST data:
        - action: 'enable' or 'disable'
        - user_ids: comma-separated list of user IDs or JSON array
        - reason: reason for bulk action (optional)
        
        Returns JSON:
        {
            "success": true/false,
            "message": "Summary message",
            "data": {
                "total": int,
                "successful": int,
                "failed": int,
                "results": [
                    {
                        "user_id": int,
                        "email": str,
                        "success": bool,
                        "message": str
                    },
                    ...
                ]
            }
        }
        """
        try:
            # Get action
            action = request.POST.get('action', '').lower()
            
            # Validate action
            if action not in ['enable', 'disable']:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid action: {action}. Must be "enable" or "disable".'
                }, status=400)
            
            # Get user IDs
            user_ids_str = request.POST.get('user_ids', '')
            
            # Parse user IDs (handle both comma-separated and JSON array)
            try:
                import json
                user_ids = json.loads(user_ids_str)
            except (json.JSONDecodeError, TypeError):
                # Try comma-separated
                user_ids = [uid.strip() for uid in user_ids_str.split(',') if uid.strip()]
            
            # Convert to integers
            try:
                user_ids = [int(uid) for uid in user_ids]
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid user IDs format. Must be comma-separated integers or JSON array.'
                }, status=400)
            
            # Validate at least one user
            if not user_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'No users selected. Please select at least one user.'
                }, status=400)
            
            # Get reason
            reason = request.POST.get('reason', '').strip()
            if not reason:
                reason = f"Bulk {action} by {request.user.get_full_name()}"
            
            # Determine target status
            is_active = (action == 'enable')
            
            # Process each user independently (Requirement 6.5)
            results = []
            successful = 0
            failed = 0
            
            for user_id in user_ids:
                try:
                    # Get user
                    user = User.objects.get(pk=user_id)
                    
                    # Skip if trying to disable self
                    if user.id == request.user.id and not is_active:
                        results.append({
                            'user_id': user_id,
                            'email': user.email,
                            'success': False,
                            'message': 'Cannot disable your own account'
                        })
                        failed += 1
                        continue
                    
                    # Update status
                    success, error_message = UserManagementService.update_user_status(
                        user=user,
                        is_active=is_active,
                        reason=reason,
                        changed_by=request.user,
                        request=request,
                        send_email=False  # Don't send individual emails for bulk operations
                    )
                    
                    if success:
                        results.append({
                            'user_id': user_id,
                            'email': user.email,
                            'success': True,
                            'message': f'Successfully {action}d'
                        })
                        successful += 1
                    else:
                        results.append({
                            'user_id': user_id,
                            'email': user.email,
                            'success': False,
                            'message': error_message or f'Failed to {action}'
                        })
                        failed += 1
                
                except User.DoesNotExist:
                    results.append({
                        'user_id': user_id,
                        'email': 'Unknown',
                        'success': False,
                        'message': 'User not found'
                    })
                    failed += 1
                
                except Exception as e:
                    logger.error(
                        f"Error processing user {user_id} in bulk action: {str(e)}",
                        exc_info=True
                    )
                    results.append({
                        'user_id': user_id,
                        'email': 'Unknown',
                        'success': False,
                        'message': 'Unexpected error'
                    })
                    failed += 1
            
            # Log bulk action
            AuditLogService.log_action(
                user=request.user,  # Log on the admin performing the action
                action='BULK_ACTION',
                performed_by=request.user,
                details={
                    'action': action,
                    'total': len(user_ids),
                    'successful': successful,
                    'failed': failed,
                    'user_ids': user_ids
                },
                reason=reason,
                request=request
            )
            
            # Build summary message
            if failed == 0:
                message = f'Successfully {action}d all {successful} user(s).'
                overall_success = True
            elif successful == 0:
                message = f'Failed to {action} all {failed} user(s).'
                overall_success = False
            else:
                message = f'{action.title()}d {successful} user(s), {failed} failed.'
                overall_success = True  # Partial success
            
            return JsonResponse({
                'success': overall_success,
                'message': message,
                'data': {
                    'total': len(user_ids),
                    'successful': successful,
                    'failed': failed,
                    'results': results
                }
            })
        
        except Exception as e:
            logger.error(
                f"Error in UserBulkActionView: {str(e)}",
                exc_info=True,
                extra={
                    'action': action if 'action' in locals() else None,
                    'performed_by': request.user.email,
                }
            )
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }, status=500)
