"""
Django management command for automated log cleanup and archival.

Usage:
    python manage.py cleanup_logs                    # Normal scheduled execution
    python manage.py cleanup_logs --manual           # Manual execution (records user)
    python manage.py cleanup_logs --dry-run          # Test run without making changes
    python manage.py cleanup_logs --manual --dry-run # Manual test run
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from log_viewer.services import LogManagementService
from log_viewer.models import LogRetentionPolicy, LogCleanupSchedule


logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Django management command for log cleanup operations.
    
    This command executes the automated log cleanup process, which includes:
    - Checking retention policies for audit and file logs
    - Exporting old logs to CSV/PDF archives
    - Deleting logs older than retention period
    - Recording operation history
    - Updating cleanup schedules
    """
    
    help = 'Execute automated log cleanup and archival based on retention policies'
    
    def add_arguments(self, parser):
        """Add command-line arguments"""
        parser.add_argument(
            '--manual',
            action='store_true',
            help='Mark this as a manual operation (vs scheduled)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate cleanup without making changes (for testing)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username of user triggering manual operation (optional)',
        )
    
    def handle(self, *args, **options):
        """Execute the cleanup operation"""
        is_manual = options.get('manual', False)
        is_dry_run = options.get('dry_run', False)
        username = options.get('user')
        
        # Determine operation type
        operation_type = 'manual' if is_manual else 'scheduled'
        
        # Output header
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Log Cleanup and Archival Operation'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f"Operation Type: {operation_type.upper()}")
        
        if is_dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        self.stdout.write('')
        
        try:
            # Check if any retention policies are enabled
            enabled_policies = LogRetentionPolicy.objects.filter(enabled=True)
            
            if not enabled_policies.exists():
                self.stdout.write(
                    self.style.WARNING('No retention policies are enabled.')
                )
                self.stdout.write(
                    'Please enable at least one retention policy in the admin interface.'
                )
                return
            
            # Display enabled policies
            self.stdout.write(self.style.SUCCESS('Enabled Retention Policies:'))
            for policy in enabled_policies:
                self.stdout.write(
                    f"  - {policy.get_log_type_display()}: "
                    f"{policy.retention_days} days, "
                    f"Export: {policy.get_export_format_display()}"
                )
            self.stdout.write('')
            
            # Check schedule if this is a scheduled operation
            if not is_manual:
                schedule = LogCleanupSchedule.objects.filter(enabled=True).first()
                if schedule:
                    self.stdout.write(
                        f"Schedule: {schedule.get_frequency_display()} "
                        f"at {schedule.execution_time.strftime('%H:%M')}"
                    )
                    if schedule.last_run:
                        self.stdout.write(
                            f"Last Run: {schedule.last_run.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                    self.stdout.write('')
            
            # Get user for manual operations
            triggered_by = None
            if is_manual and username:
                try:
                    triggered_by = User.objects.get(username=username)
                    self.stdout.write(f"Triggered by: {username}")
                    self.stdout.write('')
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"User '{username}' not found. Proceeding without user attribution.")
                    )
                    self.stdout.write('')
            
            # Dry run check
            if is_dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN: Simulating cleanup process...'))
                self.stdout.write('')
                
                # Show what would be processed
                from django.utils import timezone
                from datetime import timedelta
                
                for policy in enabled_policies:
                    cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
                    
                    if policy.log_type == 'audit':
                        from log_viewer.models import AuditLog
                        count = AuditLog.objects.filter(timestamp__lt=cutoff_date).count()
                        self.stdout.write(
                            f"  Would process {count} audit log(s) older than {cutoff_date.strftime('%Y-%m-%d')}"
                        )
                    elif policy.log_type == 'file':
                        self.stdout.write(
                            f"  Would process file logs older than {cutoff_date.strftime('%Y-%m-%d')}"
                        )
                    
                    if policy.export_before_delete:
                        self.stdout.write(
                            f"  Would export to: {policy.get_export_format_display()}"
                        )
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('DRY RUN COMPLETE - No changes were made'))
                self.stdout.write('')
                self.stdout.write('To execute the actual cleanup, run without --dry-run flag')
                return
            
            # Execute actual cleanup
            self.stdout.write(self.style.SUCCESS('Starting cleanup operation...'))
            self.stdout.write('')
            
            # Initialize service
            service = LogManagementService()
            
            # Execute cleanup
            self.stdout.write('Processing logs...')
            operation = service.execute_cleanup(
                triggered_by=triggered_by,
                operation_type=operation_type
            )
            
            # Display results
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('Operation Complete'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            
            # Status
            if operation.status == 'success':
                status_style = self.style.SUCCESS
            elif operation.status == 'partial':
                status_style = self.style.WARNING
            else:
                status_style = self.style.ERROR
            
            self.stdout.write(f"Status: {status_style(operation.status.upper())}")
            
            # Timing
            duration = (operation.completed_at - operation.started_at).total_seconds()
            self.stdout.write(f"Duration: {duration:.2f} seconds")
            self.stdout.write('')
            
            # Metrics
            self.stdout.write(self.style.SUCCESS('Metrics:'))
            self.stdout.write(f"  Audit Logs Processed: {operation.audit_logs_processed}")
            self.stdout.write(f"  Audit Logs Deleted: {operation.audit_logs_deleted}")
            self.stdout.write(f"  File Logs Processed: {operation.file_logs_processed}")
            self.stdout.write(f"  File Logs Deleted: {operation.file_logs_deleted}")
            self.stdout.write(f"  Total Processed: {operation.total_processed}")
            self.stdout.write(f"  Total Deleted: {operation.total_deleted}")
            self.stdout.write(f"  Archives Created: {operation.archives_created}")
            self.stdout.write('')
            
            # Archive files
            if operation.archive_files:
                self.stdout.write(self.style.SUCCESS('Archive Files Created:'))
                for archive_file in operation.archive_files:
                    self.stdout.write(f"  - {archive_file}")
                self.stdout.write('')
            
            # Errors
            if operation.error_message:
                self.stdout.write(self.style.ERROR('Errors:'))
                self.stdout.write(self.style.ERROR(f"  {operation.error_message}"))
                self.stdout.write('')
            
            # Next run (for scheduled operations)
            if not is_manual:
                schedule = LogCleanupSchedule.objects.filter(enabled=True).first()
                if schedule and schedule.next_run:
                    self.stdout.write(
                        f"Next Scheduled Run: {schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    self.stdout.write('')
            
            # Final message
            if operation.status == 'success':
                self.stdout.write(
                    self.style.SUCCESS('✓ Log cleanup completed successfully')
                )
            elif operation.status == 'partial':
                self.stdout.write(
                    self.style.WARNING('⚠ Log cleanup completed with some errors')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Log cleanup failed')
                )
                raise CommandError('Log cleanup operation failed')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR('OPERATION FAILED'))
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            
            logger.error(f"Log cleanup command failed: {str(e)}", exc_info=True)
            
            raise CommandError(f"Log cleanup failed: {str(e)}")
