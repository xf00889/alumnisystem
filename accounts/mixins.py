from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

logger = logging.getLogger('accounts')


class PaginationMixin:
    """
    A mixin that adds pagination functionality to any view.
    Usage:
    1. Add this mixin to your view
    2. Set items_per_page class variable (default is 10)
    3. In your get_context_data, call paginate_queryset(queryset)
    """
    items_per_page = 10

    def paginate_queryset(self, queryset, page_number=None):
        """
        Helper method to paginate any queryset
        """
        if page_number is None:
            page_number = self.request.GET.get('page', 1)
        
        paginator = Paginator(queryset, self.items_per_page)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        return page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'get_queryset'):
            queryset = self.get_queryset()
            context['page_obj'] = self.paginate_queryset(queryset)
            context['object_list'] = context['page_obj'].object_list
        return context 


class HRRequiredMixin(UserPassesTestMixin):
    """
    Mixin for class-based views that checks that the user has HR status.
    Logs unauthorized access attempts.
    Superusers always have access regardless of HR status.
    """
    
    def test_func(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        # Superusers always have access
        if user.is_superuser:
            return True
        
        # Check if user has HR status
        try:
            has_hr = user.profile.is_hr
            if not has_hr:
                logger.warning(
                    f"Unauthorized HR access attempt by user {user.id} ({user.email})",
                    extra={
                        'user_id': user.id,
                        'user_email': user.email,
                        'view': self.__class__.__name__
                    }
                )
            return has_hr
        except Exception as e:
            logger.error(
                f"Error checking HR status for user {user.id}: {str(e)}",
                extra={'user_id': user.id},
                exc_info=True
            )
            return False
    
    def handle_no_permission(self):
        """Log and raise PermissionDenied for unauthorized access"""
        logger.warning(
            f"Permission denied for user {self.request.user.id} accessing {self.__class__.__name__}",
            extra={
                'user_id': self.request.user.id,
                'view': self.__class__.__name__,
                'path': self.request.path
            }
        )
        raise PermissionDenied("You do not have permission to access this resource.")
