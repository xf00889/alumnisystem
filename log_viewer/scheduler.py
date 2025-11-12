"""
Scheduler for automated log cleanup operations.

This module provides a simple scheduler that checks LogCleanupSchedule
and executes cleanup when due. Can be run as a management command or
integrated with Django-Q/Celery.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management import call_command

from log_viewer.models import LogCleanupSchedule
from log_viewer.services import LogManagementService

logger = logging.getLogger(__name__)


class LogCleanupScheduler:
    """
    Scheduler for automated log cleanup operations.
    
    This scheduler checks if any cleanup is due based on LogCleanupSchedule
    configuration and executes the cleanup_logs management command.
    """
    
    def __init__(self):
        self.service = LogManagementService()
    
    def check_and_execute(self):
        """
        Check if cleanup is due and execute if necessary.
        
        Returns:
            dict: Execution result with status and details
        """
        try:
            # Get the active schedule
            schedule = LogCleanupSchedule.objects.filter(enabled=True).first()
            
            if not schedule:
                logger.info("No active cleanup schedule found")
                return {
                    'executed': False,
                    'reason': 'No active schedule configured'
                }
            
            # Check if cleanup is due
            now = timezone.now()
            
            if schedule.next_run is None:
                # First run - calculate next run time
                next_run_time = self.service.calculate_next_run_time(schedule)
                schedule.next_run = timezone.make_naive(next_run_time) if timezone.is_aware(next_run_time) else next_run_time
                schedule.save()
                logger.info(f"Initialized next run time: {schedule.next_run}")
                return {
                    'executed': False,
                    'reason': 'Schedule initialized',
                    'next_run': schedule.next_run
                }
            
            if now < schedule.next_run:
                logger.info(f"Cleanup not due yet. Next run: {schedule.next_run}")
                return {
                    'executed': False,
                    'reason': 'Not due yet',
                    'next_run': schedule.next_run
                }
            
            # Execute cleanup
            logger.info(f"Executing scheduled cleanup (due at {schedule.next_run})")
            
            operation = self.service.execute_cleanup(
                triggered_by=None,
                operation_type='scheduled'
            )
            
            # Update schedule
            schedule.last_run = timezone.make_naive(now) if timezone.is_aware(now) else now
            next_run_time = self.service.calculate_next_run_time(schedule)
            schedule.next_run = timezone.make_naive(next_run_time) if timezone.is_aware(next_run_time) else next_run_time
            schedule.save()
            
            logger.info(
                f"Cleanup completed. Status: {operation.status}, "
                f"Next run: {schedule.next_run}"
            )
            
            return {
                'executed': True,
                'operation_id': operation.id,
                'status': operation.status,
                'next_run': schedule.next_run,
                'metrics': {
                    'audit_logs_processed': operation.audit_logs_processed,
                    'audit_logs_deleted': operation.audit_logs_deleted,
                    'file_logs_processed': operation.file_logs_processed,
                    'file_logs_deleted': operation.file_logs_deleted,
                    'archives_created': operation.archives_created,
                }
            }
            
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}", exc_info=True)
            return {
                'executed': False,
                'error': str(e)
            }
    
    def get_next_run_info(self):
        """
        Get information about the next scheduled run.
        
        Returns:
            dict: Next run information
        """
        schedule = LogCleanupSchedule.objects.filter(enabled=True).first()
        
        if not schedule:
            return {
                'enabled': False,
                'message': 'No active schedule configured'
            }
        
        return {
            'enabled': True,
            'frequency': schedule.get_frequency_display(),
            'execution_time': schedule.execution_time.strftime('%H:%M'),
            'last_run': schedule.last_run,
            'next_run': schedule.next_run,
            'day_of_week': schedule.get_day_of_week_display() if schedule.day_of_week is not None else None,
            'day_of_month': schedule.day_of_month,
        }
