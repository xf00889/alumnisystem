"""
Signal handlers to automatically log all CRUD operations across all models.
"""
import logging
import json
from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.db import connection
from .models import AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)

# Store original values before updates
_original_values_cache = {}

# Cache for table existence check to avoid repeated database queries during migrations
_table_existence_cache = {}


def is_running_in_migration():
    """
    Detect if code is currently executing within a migration context.
    
    This function checks multiple indicators to determine if Django is currently
    running migrations:
    1. Apps registry readiness - during migrations, apps may not be fully loaded
    2. Migration executor state - checks if we're in an active migration
    
    Returns:
        bool: True if code is executing during migrations, False otherwise.
    """
    try:
        # Check 1: If apps are not ready, we're likely in a migration
        if not apps.ready:
            return True
        
        # Check 2: Try to access apps registry - if it fails, we're in migration
        try:
            apps.check_apps_ready()
        except Exception:
            return True
        
        # If all checks pass, we're not in a migration
        return False
        
    except Exception as e:
        # If detection fails, assume we're NOT in a migration (fail-safe)
        # Log at debug level to avoid noise
        logger.debug(f"Migration detection check failed: {str(e)}")
        return False


def audit_log_table_exists():
    """
    Check if the log_viewer_auditlog table exists in the database.
    
    This function queries the database schema to verify that the AuditLog table
    has been created. It uses caching to avoid repeated database queries during
    the migration phase.
    
    Returns:
        bool: True if the table exists, False otherwise.
    """
    # Check cache first
    cache_key = 'log_viewer_auditlog'
    if cache_key in _table_existence_cache:
        return _table_existence_cache[cache_key]
    
    try:
        # Query database to check if table exists
        with connection.cursor() as cursor:
            # Get list of all table names in the database
            table_names = connection.introspection.table_names(cursor)
            exists = 'log_viewer_auditlog' in table_names
            
            # Cache the result
            _table_existence_cache[cache_key] = exists
            return exists
    
    except Exception as e:
        # Specific handling for different types of database errors
        from django.db import OperationalError, DatabaseError
        
        if isinstance(e, OperationalError):
            # Database connection issues - log at ERROR level
            logger.error(
                f"Database connection error while checking audit log table existence: {str(e)}. "
                "This may indicate the database is not available or migrations haven't run yet.",
                exc_info=True
            )
        elif isinstance(e, DatabaseError):
            # General database errors - log at ERROR level
            logger.error(
                f"Database error while checking audit log table existence: {str(e)}. "
                "This may indicate schema issues or permission problems.",
                exc_info=True
            )
        else:
            # Other unexpected errors - log at ERROR level
            logger.error(
                f"Unexpected error checking if audit log table exists: {str(e)}",
                exc_info=True
            )
        
        # Cache negative result to avoid repeated failures during this execution
        _table_existence_cache[cache_key] = False
        return False


def get_model_field_values(instance, exclude_fields=None):
    """
    Get all field values from a model instance.
    Excludes sensitive fields and relationships.
    """
    exclude_fields = exclude_fields or []
    exclude_fields.extend([
        'password', 'password1', 'password2',  # Password fields
        'secret_key', 'api_key', 'token',  # API keys
        'created', 'modified', 'updated_at', 'created_at',  # Timestamps (handled separately)
    ])
    
    values = {}
    for field in instance._meta.get_fields():
        if field.name in exclude_fields:
            continue
        
        # Skip reverse relations
        if field.one_to_many or field.many_to_many or field.many_to_one:
            continue
        
        try:
            value = getattr(instance, field.name, None)
            
            # Convert to JSON-serializable format
            if value is None:
                values[field.name] = None
            elif hasattr(value, 'pk'):
                # Foreign key or related object
                values[field.name] = {
                    'id': value.pk,
                    'str': str(value)
                }
            elif isinstance(value, (str, int, float, bool)):
                values[field.name] = value
            elif isinstance(value, (list, dict)):
                values[field.name] = value
            else:
                # Convert other types to string
                values[field.name] = str(value)
        except (AttributeError, ObjectDoesNotExist):
            pass
    
    return values


def get_current_user():
    """Get the current user from thread-local storage"""
    try:
        from .middleware import get_current_user as get_user_from_middleware
        return get_user_from_middleware()
    except:
        pass
    return None


def get_request_info():
    """Get request information (IP, user agent, path)"""
    try:
        from .middleware import get_current_request
        request = get_current_request()
        if request:
            return {
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'request_path': request.path,
            }
    except:
        pass
    return {
        'ip_address': None,
        'user_agent': '',
        'request_path': '',
    }


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(pre_save)
def store_original_values(sender, instance, **kwargs):
    """
    Store original values before update so we can compare them later.
    """
    try:
        # Skip if running in migration context
        if is_running_in_migration():
            return
    except Exception as e:
        logger.debug(f"Migration detection failed in store_original_values for {sender._meta.label}: {str(e)}")
        # Fail-safe: continue execution if detection fails
    
    try:
        # Skip if audit log table doesn't exist yet
        if not audit_log_table_exists():
            return
    except Exception as e:
        logger.error(f"Table existence check failed in store_original_values for {sender._meta.label}: {str(e)}")
        # Fail-safe: skip execution if table check fails
        return
    
    # Skip for AuditLog itself
    if isinstance(instance, AuditLog):
        return
    
    # Skip for migrations
    if sender._meta.app_label == 'migrations':
        return
    
    # Skip for system models
    skip_apps = ['contenttypes', 'sessions', 'admin', 'auth', 'authtoken']
    if sender._meta.app_label in skip_apps:
        return
    
    # Only store if instance has a primary key (i.e., it's an update, not a create)
    if instance.pk:
        try:
            # Get the existing instance from database
            old_instance = sender.objects.get(pk=instance.pk)
            cache_key = f"{sender._meta.label}.{instance.pk}"
            _original_values_cache[cache_key] = get_model_field_values(old_instance)
        except (ObjectDoesNotExist, sender.DoesNotExist):
            # Instance doesn't exist yet, it's a create
            pass
        except Exception as e:
            migration_context = "during migration" if is_running_in_migration() else "in normal operation"
            logger.error(
                f"Error storing original values for {sender._meta.label} {migration_context}: {str(e)}",
                exc_info=True
            )


@receiver(post_save)
def log_create_or_update(sender, instance, created, **kwargs):
    """
    Log CREATE or UPDATE operations for all models.
    """
    try:
        # Skip if running in migration context
        if is_running_in_migration():
            return
    except Exception as e:
        logger.debug(f"Migration detection failed in log_create_or_update for {sender._meta.label}: {str(e)}")
        # Fail-safe: continue execution if detection fails
    
    try:
        # Skip if audit log table doesn't exist yet
        if not audit_log_table_exists():
            return
    except Exception as e:
        logger.error(f"Table existence check failed in log_create_or_update for {sender._meta.label}: {str(e)}")
        # Fail-safe: skip execution if table check fails
        return
    
    # Skip logging for AuditLog itself to avoid recursion
    if isinstance(instance, AuditLog):
        return
    
    # Skip logging for migrations
    if sender._meta.app_label == 'migrations':
        return
    
    # Skip logging for system models
    skip_apps = ['contenttypes', 'sessions', 'admin', 'auth', 'authtoken']
    if sender._meta.app_label in skip_apps:
        return
    
    try:
        action = 'CREATE' if created else 'UPDATE'
        content_type = ContentType.objects.get_for_model(sender)
        
        # Get user
        user = get_current_user()
        username = user.username if user and user.is_authenticated else None
        
        # Get request info
        request_info = get_request_info()
        
        # Get field values
        new_values = get_model_field_values(instance)
        
        # For updates, get changed fields
        changed_fields = []
        old_values = None
        
        if not created:
            # Get old values from cache
            cache_key = f"{sender._meta.label}.{instance.pk}"
            old_values = _original_values_cache.pop(cache_key, None)
            
            if old_values:
                # Compare to find changed fields
                for field_name, old_value in old_values.items():
                    new_value = new_values.get(field_name)
                    if old_value != new_value:
                        changed_fields.append(field_name)
            
            # If no cache, we can't determine changes
            if not old_values:
                changed_fields = None
        
        # Create message
        object_repr = str(instance)[:200]  # Limit length
        if created:
            message = f"{action}: {sender._meta.verbose_name} '{object_repr}' created"
        else:
            if changed_fields:
                message = f"{action}: {sender._meta.verbose_name} '{object_repr}' updated - Fields: {', '.join(changed_fields[:5])}"
            else:
                message = f"{action}: {sender._meta.verbose_name} '{object_repr}' updated"
        
        # Create audit log entry
        audit_log = AuditLog.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            action=action,
            model_name=sender._meta.model_name,
            app_label=sender._meta.app_label,
            user=user if user and user.is_authenticated else None,
            username=username,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields if changed_fields else None,
            ip_address=request_info.get('ip_address'),
            user_agent=request_info.get('user_agent', '')[:500],  # Limit length
            request_path=request_info.get('request_path', '')[:500],
            message=message,
            timestamp=timezone.now(),
        )
        
        # Also log to file logger
        logger.info(
            f"AUDIT {action}: {sender._meta.app_label}.{sender._meta.model_name} "
            f"#{instance.pk} by {username or 'Anonymous'} - {message}"
        )
        
    except Exception as e:
        # Don't let logging errors break the application
        migration_context = "during migration" if is_running_in_migration() else "in normal operation"
        logger.error(
            f"Error creating audit log for {sender._meta.label} {migration_context}: {str(e)}",
            exc_info=True
        )


@receiver(pre_delete)
def log_pre_delete(sender, instance, **kwargs):
    """
    Store original values before deletion so we can log them.
    """
    try:
        # Skip if running in migration context
        if is_running_in_migration():
            return
    except Exception as e:
        logger.debug(f"Migration detection failed in log_pre_delete for {sender._meta.label}: {str(e)}")
        # Fail-safe: continue execution if detection fails
    
    try:
        # Skip if audit log table doesn't exist yet
        if not audit_log_table_exists():
            return
    except Exception as e:
        logger.error(f"Table existence check failed in log_pre_delete for {sender._meta.label}: {str(e)}")
        # Fail-safe: skip execution if table check fails
        return
    
    # Skip logging for AuditLog itself
    if isinstance(instance, AuditLog):
        return
    
    # Skip logging for migrations
    if sender._meta.app_label == 'migrations':
        return
    
    # Skip logging for system models
    skip_apps = ['contenttypes', 'sessions', 'admin', 'auth', 'authtoken']
    if sender._meta.app_label in skip_apps:
        return
    
    try:
        # Store original values for deletion logging
        cache_key = f"{sender._meta.label}.{instance.pk}"
        _original_values_cache[cache_key] = get_model_field_values(instance)
    except Exception as e:
        migration_context = "during migration" if is_running_in_migration() else "in normal operation"
        logger.error(
            f"Error storing pre-delete values for {sender._meta.label} {migration_context}: {str(e)}",
            exc_info=True
        )


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    """
    Log DELETE operations for all models.
    """
    try:
        # Skip if running in migration context
        if is_running_in_migration():
            return
    except Exception as e:
        logger.debug(f"Migration detection failed in log_delete for {sender._meta.label}: {str(e)}")
        # Fail-safe: continue execution if detection fails
    
    try:
        # Skip if audit log table doesn't exist yet
        if not audit_log_table_exists():
            return
    except Exception as e:
        logger.error(f"Table existence check failed in log_delete for {sender._meta.label}: {str(e)}")
        # Fail-safe: skip execution if table check fails
        return
    
    # Skip logging for AuditLog itself
    if isinstance(instance, AuditLog):
        return
    
    # Skip logging for migrations
    if sender._meta.app_label == 'migrations':
        return
    
    # Skip logging for system models
    skip_apps = ['contenttypes', 'sessions', 'admin', 'auth', 'authtoken']
    if sender._meta.app_label in skip_apps:
        return
    
    try:
        content_type = ContentType.objects.get_for_model(sender)
        
        # Get user
        user = get_current_user()
        username = user.username if user and user.is_authenticated else None
        
        # Get request info
        request_info = get_request_info()
        
        # Get old values from cache
        cache_key = f"{sender._meta.label}.{instance.pk}"
        old_values = _original_values_cache.pop(cache_key, None)
        
        # Get object representation before deletion
        try:
            object_repr = str(instance)[:200]
        except:
            object_repr = f"{sender._meta.verbose_name} #{instance.pk}"
        
        # Create message
        message = f"DELETE: {sender._meta.verbose_name} '{object_repr}' deleted"
        
        # Create audit log entry
        audit_log = AuditLog.objects.create(
            content_type=content_type,
            object_id=instance.pk if hasattr(instance, 'pk') and instance.pk else None,
            action='DELETE',
            model_name=sender._meta.model_name,
            app_label=sender._meta.app_label,
            user=user if user and user.is_authenticated else None,
            username=username,
            old_values=old_values,
            new_values=None,
            changed_fields=None,
            ip_address=request_info.get('ip_address'),
            user_agent=request_info.get('user_agent', '')[:500],
            request_path=request_info.get('request_path', '')[:500],
            message=message,
            timestamp=timezone.now(),
        )
        
        # Also log to file logger
        logger.warning(
            f"AUDIT DELETE: {sender._meta.app_label}.{sender._meta.model_name} "
            f"#{instance.pk if hasattr(instance, 'pk') else '?'} by {username or 'Anonymous'} - {message}"
        )
        
    except Exception as e:
        # Don't let logging errors break the application
        migration_context = "during migration" if is_running_in_migration() else "in normal operation"
        logger.error(
            f"Error creating audit log for delete {sender._meta.label} {migration_context}: {str(e)}",
            exc_info=True
        )

