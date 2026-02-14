"""
Service layer for log management operations.
Handles cleanup, archival, and export of audit and file logs.
"""

import os
import csv
import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

from .models import (
    AuditLog,
    LogRetentionPolicy,
    LogCleanupSchedule,
    LogOperationHistory,
    ArchiveStorageConfig
)


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending admin notifications about log management operations"""
    
    @staticmethod
    def notify_cleanup_success(operation_history):
        """
        Send notification for successful cleanup operation.
        
        Args:
            operation_history: LogOperationHistory instance
        """
        try:
            from django.contrib import messages
            from django.contrib.auth import get_user_model
            
            logger.info(
                f"Cleanup operation completed successfully: "
                f"Processed {operation_history.total_processed} records, "
                f"Deleted {operation_history.total_deleted} records, "
                f"Created {operation_history.archives_created} archives"
            )
            
            # For manual operations, we can add a message to the user's session
            # For scheduled operations, we log the success
            if operation_history.operation_type == 'manual' and operation_history.triggered_by:
                # This will be displayed when the user next loads an admin page
                # Note: In practice, this would be handled by the view that triggers the operation
                pass
            
            # Log success for monitoring
            logger.info(
                f"Log cleanup success notification: "
                f"Type={operation_history.operation_type}, "
                f"Status={operation_history.status}, "
                f"Total Processed={operation_history.total_processed}, "
                f"Total Deleted={operation_history.total_deleted}, "
                f"Archives Created={operation_history.archives_created}"
            )
            
        except Exception as e:
            logger.error(f"Error sending cleanup success notification: {str(e)}")
    
    @staticmethod
    def notify_cleanup_failure(operation_history):
        """
        Send high-priority notification for failed cleanup operation.
        
        Args:
            operation_history: LogOperationHistory instance
        """
        try:
            from django.contrib.auth import get_user_model
            
            error_msg = (
                f"CRITICAL: Log cleanup operation failed!\n"
                f"Operation Type: {operation_history.get_operation_type_display()}\n"
                f"Started: {operation_history.started_at}\n"
                f"Error: {operation_history.error_message}\n"
                f"Records Processed: {operation_history.total_processed}\n"
                f"Records Deleted: {operation_history.total_deleted}"
            )
            
            # Log critical error
            logger.error(error_msg)
            
            # In a production system, you might want to:
            # 1. Send email to admins
            # 2. Create a Django admin notification
            # 3. Send to monitoring system (Sentry, etc.)
            
            # For now, we'll log it prominently
            logger.critical(
                f"Log cleanup failure notification: "
                f"Type={operation_history.operation_type}, "
                f"Error={operation_history.error_message}"
            )
            
            # Optionally send email to superusers
            try:
                User = get_user_model()
                superusers = User.objects.filter(is_superuser=True, is_active=True)
                
                if superusers.exists():
                    from django.core.mail import mail_admins
                    
                    subject = "CRITICAL: Log Cleanup Operation Failed"
                    message = error_msg
                    
                    # This will send to ADMINS in settings.py
                    mail_admins(
                        subject=subject,
                        message=message,
                        fail_silently=True  # Don't raise exception if email fails
                    )
                    
                    logger.info(f"Sent failure notification email to {superusers.count()} admins")
            except Exception as email_error:
                logger.error(f"Failed to send email notification: {str(email_error)}")
            
        except Exception as e:
            logger.error(f"Error sending cleanup failure notification: {str(e)}")
    
    @staticmethod
    def notify_storage_warning(storage_config):
        """
        Send warning notification when storage reaches warning threshold (80%).
        
        Args:
            storage_config: ArchiveStorageConfig instance
        """
        try:
            usage_percent = storage_config.usage_percent
            
            warning_msg = (
                f"WARNING: Archive storage approaching limit!\n"
                f"Current Usage: {storage_config.current_size_gb} GB / "
                f"{storage_config.max_storage_gb} GB ({usage_percent:.1f}%)\n"
                f"Warning Threshold: {storage_config.warning_threshold_percent}%\n"
                f"Action Required: Consider increasing storage limit or cleaning old archives"
            )
            
            # Log warning
            logger.warning(warning_msg)
            
            logger.warning(
                f"Storage warning notification: "
                f"Usage={usage_percent:.1f}%, "
                f"Current={storage_config.current_size_gb}GB, "
                f"Max={storage_config.max_storage_gb}GB"
            )
            
            # Optionally send email to admins
            try:
                from django.core.mail import mail_admins
                
                subject = "WARNING: Archive Storage Approaching Limit"
                message = warning_msg
                
                mail_admins(
                    subject=subject,
                    message=message,
                    fail_silently=True
                )
                
                logger.info("Sent storage warning email to admins")
            except Exception as email_error:
                logger.error(f"Failed to send storage warning email: {str(email_error)}")
            
        except Exception as e:
            logger.error(f"Error sending storage warning notification: {str(e)}")
    
    @staticmethod
    def notify_storage_critical(storage_config):
        """
        Send critical notification when storage reaches critical threshold (95%).
        Archival will be paused at this level.
        
        Args:
            storage_config: ArchiveStorageConfig instance
        """
        try:
            usage_percent = storage_config.usage_percent
            
            critical_msg = (
                f"CRITICAL: Archive storage at critical level!\n"
                f"Current Usage: {storage_config.current_size_gb} GB / "
                f"{storage_config.max_storage_gb} GB ({usage_percent:.1f}%)\n"
                f"Critical Threshold: {storage_config.critical_threshold_percent}%\n"
                f"AUTOMATIC ARCHIVAL HAS BEEN PAUSED!\n"
                f"Immediate Action Required: Increase storage limit or remove old archives\n"
                f"Note: Log deletion will continue, but exports will be skipped"
            )
            
            # Log critical error
            logger.critical(critical_msg)
            
            logger.critical(
                f"Storage critical notification: "
                f"Usage={usage_percent:.1f}%, "
                f"Current={storage_config.current_size_gb}GB, "
                f"Max={storage_config.max_storage_gb}GB, "
                f"ARCHIVAL PAUSED"
            )
            
            # Send email to admins with high priority
            try:
                from django.core.mail import mail_admins
                
                subject = "CRITICAL: Archive Storage Full - Archival Paused"
                message = critical_msg
                
                mail_admins(
                    subject=subject,
                    message=message,
                    fail_silently=True
                )
                
                logger.info("Sent critical storage notification email to admins")
            except Exception as email_error:
                logger.error(f"Failed to send critical storage email: {str(email_error)}")
            
        except Exception as e:
            logger.error(f"Error sending storage critical notification: {str(e)}")


class LogManagementService:
    """Service for managing log cleanup and archival operations"""
    
    def __init__(self):
        self.operation_history = None
        self.logger = logging.getLogger(__name__)
        self.archive_files = []
        self.errors = []
    
    def execute_cleanup(self, triggered_by=None, operation_type='scheduled'):
        """
        Main entry point for log cleanup operations.
        
        Args:
            triggered_by: User who triggered manual operation (None for scheduled)
            operation_type: 'scheduled' or 'manual'
        
        Returns:
            LogOperationHistory instance
        """
        self.logger.info(f"Starting {operation_type} log cleanup operation")
        
        # Create operation history record
        self.operation_history = LogOperationHistory.objects.create(
            operation_type=operation_type,
            status='failed',  # Default to failed, update on success
            started_at=timezone.now(),
            triggered_by=triggered_by
        )
        
        try:
            # Check storage limits before proceeding
            storage_status = self.check_storage_limits()
            if storage_status == 'critical':
                self.logger.warning("Archive storage at critical level, skipping export")
                # Continue with deletion only, no export
                export_enabled = False
            else:
                export_enabled = True
            
            # Get enabled retention policies
            audit_policy = LogRetentionPolicy.objects.filter(
                log_type='audit',
                enabled=True
            ).first()
            
            file_policy = LogRetentionPolicy.objects.filter(
                log_type='file',
                enabled=True
            ).first()
            
            # Process audit logs if policy exists
            if audit_policy:
                self.logger.info("Processing audit logs")
                try:
                    processed, deleted, archives = self.process_audit_logs(
                        audit_policy,
                        export_enabled=export_enabled
                    )
                    self.operation_history.audit_logs_processed = processed
                    self.operation_history.audit_logs_deleted = deleted
                    self.archive_files.extend(archives)
                except Exception as e:
                    self.logger.error(f"Error processing audit logs: {str(e)}")
                    self.errors.append(f"Audit logs: {str(e)}")
            
            # Process file logs if policy exists
            if file_policy:
                self.logger.info("Processing file logs")
                try:
                    processed, deleted, archives = self.process_file_logs(
                        file_policy,
                        export_enabled=export_enabled
                    )
                    self.operation_history.file_logs_processed = processed
                    self.operation_history.file_logs_deleted = deleted
                    self.archive_files.extend(archives)
                except Exception as e:
                    self.logger.error(f"Error processing file logs: {str(e)}")
                    self.errors.append(f"File logs: {str(e)}")
            
            # Update operation history
            self.operation_history.archives_created = len(self.archive_files)
            self.operation_history.archive_files = self.archive_files
            self.operation_history.completed_at = timezone.now()
            
            # Determine final status
            if self.errors:
                if self.operation_history.total_processed > 0:
                    self.operation_history.status = 'partial'
                    self.operation_history.error_message = '; '.join(self.errors)
                else:
                    self.operation_history.status = 'failed'
                    self.operation_history.error_message = '; '.join(self.errors)
            else:
                self.operation_history.status = 'success'
            
            self.operation_history.save()
            
            # Update schedule next run time if this was scheduled
            if operation_type == 'scheduled':
                schedule = LogCleanupSchedule.objects.filter(enabled=True).first()
                if schedule:
                    schedule.last_run = timezone.now()
                    schedule.next_run = self.calculate_next_run_time(schedule)
                    schedule.save()
            
            # Update storage size
            self.update_storage_size()
            
            self.logger.info(
                f"Cleanup completed: {self.operation_history.status} - "
                f"Processed: {self.operation_history.total_processed}, "
                f"Deleted: {self.operation_history.total_deleted}, "
                f"Archives: {self.operation_history.archives_created}"
            )
            
            # Send notifications based on operation status
            if self.operation_history.status == 'success':
                NotificationService.notify_cleanup_success(self.operation_history)
            elif self.operation_history.status in ['failed', 'partial']:
                NotificationService.notify_cleanup_failure(self.operation_history)
            
            return self.operation_history
            
        except Exception as e:
            self.logger.error(f"Critical error in cleanup operation: {str(e)}")
            self.operation_history.status = 'failed'
            self.operation_history.error_message = str(e)
            self.operation_history.completed_at = timezone.now()
            self.operation_history.save()
            raise

    def process_audit_logs(self, policy, export_enabled=True):
        """
        Process audit logs according to retention policy.
        
        Args:
            policy: LogRetentionPolicy instance for audit logs
            export_enabled: Whether to export before deletion
        
        Returns:
            Tuple of (processed_count, deleted_count, archive_files)
        """
        cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
        
        # Ensure cutoff_date matches USE_TZ setting
        if not settings.USE_TZ and timezone.is_aware(cutoff_date):
            cutoff_date = timezone.make_naive(cutoff_date)
        
        self.logger.info(f"Processing audit logs older than {cutoff_date}")
        
        # Query logs older than retention period
        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        processed_count = old_logs.count()
        
        if processed_count == 0:
            self.logger.info("No audit logs to process")
            return 0, 0, []
        
        self.logger.info(f"Found {processed_count} audit logs to process")
        archive_files = []
        
        # Export before deletion if enabled
        if export_enabled and policy.export_before_delete:
            try:
                # Process in batches for performance
                batch_size = 1000
                all_logs = []
                
                for i in range(0, processed_count, batch_size):
                    batch = old_logs[i:i + batch_size]
                    all_logs.extend(list(batch))
                    self.logger.debug(f"Loaded batch {i // batch_size + 1}")
                
                # Export to CSV if requested
                if policy.export_format in ['csv', 'both']:
                    csv_file = self._create_archive_filepath(policy, 'csv')
                    self.export_audit_logs_to_csv(all_logs, csv_file)
                    archive_files.append(csv_file)
                    self.logger.info(f"Exported audit logs to CSV: {csv_file}")
                
                # Export to PDF if requested
                if policy.export_format in ['pdf', 'both']:
                    pdf_file = self._create_archive_filepath(policy, 'pdf')
                    self.export_audit_logs_to_pdf(all_logs, pdf_file)
                    archive_files.append(pdf_file)
                    self.logger.info(f"Exported audit logs to PDF: {pdf_file}")
                    
            except Exception as e:
                self.logger.error(f"Error exporting audit logs: {str(e)}")
                raise Exception(f"Export failed: {str(e)}")
        
        # Delete old logs
        deleted_count = self.delete_old_audit_logs(cutoff_date)
        
        return processed_count, deleted_count, archive_files
    
    def delete_old_audit_logs(self, cutoff_date):
        """
        Delete audit logs older than cutoff date with transaction support.
        
        Args:
            cutoff_date: DateTime threshold for deletion
        
        Returns:
            Number of records deleted
        """
        try:
            with transaction.atomic():
                # Delete in batches for better performance
                batch_size = 1000
                total_deleted = 0
                
                while True:
                    # Get IDs of logs to delete in this batch
                    log_ids = list(
                        AuditLog.objects.filter(
                            timestamp__lt=cutoff_date
                        ).values_list('id', flat=True)[:batch_size]
                    )
                    
                    if not log_ids:
                        break
                    
                    # Delete the batch
                    deleted = AuditLog.objects.filter(id__in=log_ids).delete()[0]
                    total_deleted += deleted
                    self.logger.debug(f"Deleted batch of {deleted} audit logs")
                
                self.logger.info(f"Deleted {total_deleted} audit logs")
                return total_deleted
                
        except Exception as e:
            self.logger.error(f"Error deleting audit logs: {str(e)}")
            raise

    def process_file_logs(self, policy, export_enabled=True):
        """
        Process file-based logs according to retention policy.
        
        Args:
            policy: LogRetentionPolicy instance for file logs
            export_enabled: Whether to export before deletion
        
        Returns:
            Tuple of (processed_count, deleted_count, archive_files)
        """
        cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
        
        # Ensure cutoff_date matches USE_TZ setting
        if not settings.USE_TZ and timezone.is_aware(cutoff_date):
            cutoff_date = timezone.make_naive(cutoff_date)
        
        self.logger.info(f"Processing file logs older than {cutoff_date}")
        
        # Get log file paths
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        log_files = ['alumni_system.log', 'errors.log']
        
        total_processed = 0
        total_deleted = 0
        archive_files = []
        
        for log_filename in log_files:
            log_path = os.path.join(log_dir, log_filename)
            
            if not os.path.exists(log_path):
                self.logger.warning(f"Log file not found: {log_path}")
                continue
            
            try:
                # Parse log file and extract old entries
                old_entries, remaining_entries = self._parse_log_file(log_path, cutoff_date)
                
                if not old_entries:
                    self.logger.info(f"No old entries in {log_filename}")
                    continue
                
                processed_count = len(old_entries)
                total_processed += processed_count
                self.logger.info(f"Found {processed_count} old entries in {log_filename}")
                
                # Export before deletion if enabled
                if export_enabled and policy.export_before_delete:
                    # Export to CSV if requested
                    if policy.export_format in ['csv', 'both']:
                        csv_file = self._create_archive_filepath(
                            policy, 'csv', suffix=f"_{log_filename.replace('.log', '')}"
                        )
                        self.export_file_logs_to_csv(old_entries, csv_file, log_filename)
                        archive_files.append(csv_file)
                        self.logger.info(f"Exported {log_filename} to CSV: {csv_file}")
                    
                    # Export to PDF if requested
                    if policy.export_format in ['pdf', 'both']:
                        pdf_file = self._create_archive_filepath(
                            policy, 'pdf', suffix=f"_{log_filename.replace('.log', '')}"
                        )
                        self.export_file_logs_to_pdf(old_entries, pdf_file, log_filename)
                        archive_files.append(pdf_file)
                        self.logger.info(f"Exported {log_filename} to PDF: {pdf_file}")
                
                # Delete old entries by rewriting file
                deleted_count = self.delete_old_file_logs(log_path, remaining_entries)
                total_deleted += deleted_count
                
            except Exception as e:
                self.logger.error(f"Error processing {log_filename}: {str(e)}")
                raise Exception(f"File log processing failed for {log_filename}: {str(e)}")
        
        return total_processed, total_deleted, archive_files
    
    def _parse_log_file(self, log_path, cutoff_date):
        """
        Parse log file and separate old entries from recent ones.
        
        Args:
            log_path: Path to log file
            cutoff_date: DateTime threshold
        
        Returns:
            Tuple of (old_entries, remaining_entries)
        """
        old_entries = []
        remaining_entries = []
        
        # Common log timestamp patterns
        timestamp_patterns = [
            # ISO format: 2025-11-12 14:30:22,123
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            # Alternative: [2025-11-12 14:30:22]
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]',
        ]
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_entry = []
                current_timestamp = None
                
                for line in f:
                    # Try to extract timestamp from line
                    timestamp = None
                    for pattern in timestamp_patterns:
                        match = re.search(pattern, line)
                        if match:
                            try:
                                timestamp_str = match.group(1)
                                # Parse timestamp (handle both with and without milliseconds)
                                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S,%f']:
                                    try:
                                        timestamp = datetime.strptime(timestamp_str, fmt)
                                        # Make timezone aware/naive to match cutoff_date
                                        if settings.USE_TZ:
                                            if timezone.is_naive(timestamp):
                                                timestamp = timezone.make_aware(timestamp)
                                        else:
                                            if timezone.is_aware(timestamp):
                                                timestamp = timezone.make_naive(timestamp)
                                        break
                                    except ValueError:
                                        continue
                                break
                            except Exception:
                                continue
                    
                    # If we found a timestamp, this is a new log entry
                    if timestamp:
                        # Save previous entry if exists
                        if current_entry:
                            entry_text = ''.join(current_entry)
                            if current_timestamp and current_timestamp < cutoff_date:
                                old_entries.append(entry_text)
                            else:
                                remaining_entries.append(entry_text)
                        
                        # Start new entry
                        current_entry = [line]
                        current_timestamp = timestamp
                    else:
                        # Continuation of current entry
                        current_entry.append(line)
                
                # Don't forget the last entry
                if current_entry:
                    entry_text = ''.join(current_entry)
                    if current_timestamp and current_timestamp < cutoff_date:
                        old_entries.append(entry_text)
                    else:
                        remaining_entries.append(entry_text)
        
        except Exception as e:
            self.logger.error(f"Error parsing log file {log_path}: {str(e)}")
            raise
        
        return old_entries, remaining_entries
    
    def delete_old_file_logs(self, log_path, remaining_entries):
        """
        Delete old file log entries by rewriting the log file.
        Creates a backup before modification.
        
        Args:
            log_path: Path to log file
            remaining_entries: List of log entries to keep
        
        Returns:
            Number of entries deleted
        """
        try:
            # Create backup
            backup_path = f"{log_path}.backup"
            if os.path.exists(log_path):
                import shutil
                shutil.copy2(log_path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Count original entries
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Rewrite file with remaining entries
            with open(log_path, 'w', encoding='utf-8') as f:
                f.writelines(remaining_entries)
            
            deleted_count = len(original_content.split('\n')) - len(''.join(remaining_entries).split('\n'))
            self.logger.info(f"Deleted approximately {deleted_count} lines from {log_path}")
            
            # Remove backup after 24 hours (in production, this would be a scheduled task)
            # For now, we keep it
            
            return max(0, deleted_count)
            
        except Exception as e:
            self.logger.error(f"Error deleting old file logs: {str(e)}")
            # Restore from backup if exists
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, log_path)
                self.logger.info("Restored from backup due to error")
            raise

    def export_audit_logs_to_csv(self, logs, filepath):
        """
        Export audit logs to CSV format.
        
        Args:
            logs: List of AuditLog instances
            filepath: Full path to output CSV file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Timestamp',
                    'Action',
                    'Model',
                    'App',
                    'Object ID',
                    'User',
                    'IP Address',
                    'Message',
                    'Changed Fields',
                    'Old Values',
                    'New Values'
                ])
                
                # Write data rows
                for log in logs:
                    writer.writerow([
                        log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        log.action,
                        log.model_name,
                        log.app_label,
                        log.object_id,
                        log.username or 'Anonymous',
                        log.ip_address or '',
                        log.message or '',
                        ', '.join(log.changed_fields) if log.changed_fields else '',
                        str(log.old_values) if log.old_values else '',
                        str(log.new_values) if log.new_values else ''
                    ])
            
            self.logger.info(f"Exported {len(logs)} audit logs to CSV: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting audit logs to CSV: {str(e)}")
            raise
    
    def export_file_logs_to_csv(self, log_entries, filepath, log_filename):
        """
        Export file logs to CSV format.
        
        Args:
            log_entries: List of log entry strings
            filepath: Full path to output CSV file
            log_filename: Name of the source log file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['Source File', 'Log Entry'])
                
                # Write data rows
                for entry in log_entries:
                    # Clean up entry (remove extra newlines)
                    clean_entry = entry.strip()
                    writer.writerow([log_filename, clean_entry])
            
            self.logger.info(f"Exported {len(log_entries)} file log entries to CSV: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting file logs to CSV: {str(e)}")
            raise
    
    def _create_archive_filepath(self, policy, extension, suffix=''):
        """
        Create archive file path with proper naming convention.
        
        Args:
            policy: LogRetentionPolicy instance
            extension: File extension (csv or pdf)
            suffix: Optional suffix for filename
        
        Returns:
            Full path to archive file
        """
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create filename: logs_archive_{type}_{YYYYMMDD}_{HHMMSS}{suffix}.{ext}
        filename = f"logs_archive_{policy.log_type}_{timestamp}{suffix}.{extension}"
        
        # Create directory structure: YYYY/MM/
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')
        
        # Build full path
        archive_dir = os.path.join(
            settings.MEDIA_ROOT,
            policy.archive_path,
            year,
            month
        )
        
        # Ensure directory exists
        os.makedirs(archive_dir, exist_ok=True)
        
        filepath = os.path.join(archive_dir, filename)
        
        return filepath

    def export_audit_logs_to_pdf(self, logs, filepath):
        """
        Export audit logs to PDF format with proper styling.
        
        Args:
            logs: List of AuditLog instances
            filepath: Full path to output PDF file
        """
        try:
            # Import LogoHeaderService
            from core.export_utils import LogoHeaderService
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Get logo path
            logo_path = LogoHeaderService.get_logo_path()
            
            # Create PDF document with increased top margin for header
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=80,
                bottomMargin=30
            )
            
            # Container for PDF elements
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Add title
            title = Paragraph("Audit Logs Archive", title_style)
            elements.append(title)
            
            # Add metadata
            metadata_style = styles['Normal']
            metadata = Paragraph(
                f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
                f"<b>Total Records:</b> {len(logs)}",
                metadata_style
            )
            elements.append(metadata)
            elements.append(Spacer(1, 20))
            
            # Prepare table data
            table_data = [[
                'Timestamp',
                'Action',
                'Model',
                'User',
                'Message'
            ]]
            
            for log in logs:
                table_data.append([
                    log.timestamp.strftime('%Y-%m-%d\n%H:%M:%S'),
                    log.action,
                    f"{log.app_label}.\n{log.model_name}",
                    log.username or 'Anonymous',
                    (log.message or '')[:50] + ('...' if log.message and len(log.message) > 50 else '')
                ])
            
            # Create table
            table = Table(table_data, colWidths=[1.2*inch, 0.8*inch, 1.2*inch, 1*inch, 2*inch])
            
            # Style table
            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            
            elements.append(table)
            
            # Create custom canvas class for header
            class HeaderCanvas(canvas.Canvas):
                def __init__(self, *args, **kwargs):
                    canvas.Canvas.__init__(self, *args, **kwargs)
                
                def showPage(self):
                    # Add logo header to each page
                    LogoHeaderService.add_pdf_header(
                        self, doc, logo_path,
                        title="NORSU Alumni System - Audit Logs"
                    )
                    canvas.Canvas.showPage(self)
            
            # Build PDF with custom canvas
            doc.build(elements, canvasmaker=HeaderCanvas)
            
            self.logger.info(f"Exported {len(logs)} audit logs to PDF: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting audit logs to PDF: {str(e)}")
            raise
    
    def export_file_logs_to_pdf(self, log_entries, filepath, log_filename):
        """
        Export file logs to PDF format with proper styling.
        
        Args:
            log_entries: List of log entry strings
            filepath: Full path to output PDF file
            log_filename: Name of the source log file
        """
        try:
            # Import LogoHeaderService
            from core.export_utils import LogoHeaderService
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Get logo path
            logo_path = LogoHeaderService.get_logo_path()
            
            # Create PDF document with increased top margin for header
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=80,
                bottomMargin=30
            )
            
            # Container for PDF elements
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Add title
            title = Paragraph(f"File Logs Archive: {log_filename}", title_style)
            elements.append(title)
            
            # Add metadata
            metadata_style = styles['Normal']
            metadata = Paragraph(
                f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
                f"<b>Source File:</b> {log_filename}<br/>"
                f"<b>Total Entries:</b> {len(log_entries)}",
                metadata_style
            )
            elements.append(metadata)
            elements.append(Spacer(1, 20))
            
            # Add log entries
            log_style = ParagraphStyle(
                'LogEntry',
                parent=styles['Code'],
                fontSize=7,
                leading=10,
                leftIndent=10,
                rightIndent=10,
                spaceAfter=5,
                wordWrap='CJK'
            )
            
            for i, entry in enumerate(log_entries[:500]):  # Limit to 500 entries per PDF
                # Clean and escape entry
                clean_entry = entry.strip().replace('<', '&lt;').replace('>', '&gt;')
                
                # Truncate very long entries
                if len(clean_entry) > 500:
                    clean_entry = clean_entry[:500] + '...'
                
                entry_para = Paragraph(clean_entry, log_style)
                elements.append(entry_para)
                
                # Add page break every 50 entries
                if (i + 1) % 50 == 0 and i < len(log_entries) - 1:
                    elements.append(PageBreak())
            
            # Add note if entries were truncated
            if len(log_entries) > 500:
                note_style = styles['Italic']
                note = Paragraph(
                    f"<i>Note: Only first 500 of {len(log_entries)} entries shown. "
                    f"See CSV export for complete data.</i>",
                    note_style
                )
                elements.append(Spacer(1, 20))
                elements.append(note)
            
            # Create custom canvas class for header
            class HeaderCanvas(canvas.Canvas):
                def __init__(self, *args, **kwargs):
                    canvas.Canvas.__init__(self, *args, **kwargs)
                
                def showPage(self):
                    # Add logo header to each page
                    LogoHeaderService.add_pdf_header(
                        self, doc, logo_path,
                        title="NORSU Alumni System - File Logs"
                    )
                    canvas.Canvas.showPage(self)
            
            # Build PDF with custom canvas
            doc.build(elements, canvasmaker=HeaderCanvas)
            
            self.logger.info(f"Exported {len(log_entries)} file log entries to PDF: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting file logs to PDF: {str(e)}")
            raise

    def check_storage_limits(self):
        """
        Check if archive storage is within limits.
        
        Returns:
            Status string: 'normal', 'warning', or 'critical'
        """
        try:
            storage_config = ArchiveStorageConfig.objects.first()
            
            if not storage_config:
                # Create default config if doesn't exist
                storage_config = ArchiveStorageConfig.objects.create()
            
            # Calculate current storage size
            archive_base = os.path.join(settings.MEDIA_ROOT, 'logs/archives')
            
            if not os.path.exists(archive_base):
                storage_config.current_size_gb = Decimal('0.0')
                storage_config.last_size_check = timezone.now()
                storage_config.save()
                return 'normal'
            
            # Calculate total size in bytes
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(archive_base):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
            
            # Convert to GB
            size_gb = Decimal(str(total_size / (1024 ** 3)))
            
            # Update storage config
            storage_config.current_size_gb = size_gb
            storage_config.last_size_check = timezone.now()
            storage_config.save()
            
            # Check thresholds
            usage_percent = storage_config.usage_percent
            
            if usage_percent >= storage_config.critical_threshold_percent:
                self.logger.warning(
                    f"Archive storage at critical level: {usage_percent:.1f}% "
                    f"({size_gb} GB / {storage_config.max_storage_gb} GB)"
                )
                # Send critical notification
                NotificationService.notify_storage_critical(storage_config)
                return 'critical'
            elif usage_percent >= storage_config.warning_threshold_percent:
                self.logger.warning(
                    f"Archive storage at warning level: {usage_percent:.1f}% "
                    f"({size_gb} GB / {storage_config.max_storage_gb} GB)"
                )
                # Send warning notification
                NotificationService.notify_storage_warning(storage_config)
                return 'warning'
            else:
                self.logger.info(
                    f"Archive storage normal: {usage_percent:.1f}% "
                    f"({size_gb} GB / {storage_config.max_storage_gb} GB)"
                )
                return 'normal'
                
        except Exception as e:
            self.logger.error(f"Error checking storage limits: {str(e)}")
            return 'normal'  # Default to normal on error
    
    def update_storage_size(self):
        """
        Update the current storage size in ArchiveStorageConfig.
        Called after cleanup operations.
        """
        try:
            storage_config = ArchiveStorageConfig.objects.first()
            
            if not storage_config:
                storage_config = ArchiveStorageConfig.objects.create()
            
            # Calculate current storage size
            archive_base = os.path.join(settings.MEDIA_ROOT, 'logs/archives')
            
            if not os.path.exists(archive_base):
                storage_config.current_size_gb = Decimal('0.0')
                storage_config.last_size_check = timezone.now()
                storage_config.save()
                return
            
            # Calculate total size in bytes
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(archive_base):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
            
            # Convert to GB
            size_gb = Decimal(str(total_size / (1024 ** 3)))
            
            # Update storage config
            storage_config.current_size_gb = size_gb
            storage_config.last_size_check = timezone.now()
            storage_config.save()
            
            self.logger.info(f"Updated storage size: {size_gb} GB")
            
        except Exception as e:
            self.logger.error(f"Error updating storage size: {str(e)}")

    def calculate_next_run_time(self, schedule):
        """
        Calculate next scheduled run time based on frequency.
        
        Args:
            schedule: LogCleanupSchedule instance
        
        Returns:
            DateTime of next scheduled run (timezone-aware if USE_TZ=True, naive otherwise)
        """
        from django.conf import settings
        
        # Get current time
        now = timezone.now()
        
        # Helper function to create datetime with proper timezone handling
        def make_datetime(date, time):
            naive_dt = datetime.combine(date, time)
            if settings.USE_TZ:
                # Make timezone aware if USE_TZ is True
                if timezone.is_naive(naive_dt):
                    return timezone.make_aware(naive_dt)
                return naive_dt
            else:
                # Keep naive if USE_TZ is False
                if timezone.is_aware(naive_dt):
                    return timezone.make_naive(naive_dt)
                return naive_dt
        
        execution_time = schedule.execution_time
        
        if schedule.frequency == 'daily':
            # Next run is today at execution_time if not passed, otherwise tomorrow
            next_run = make_datetime(now.date(), execution_time)
            
            if next_run <= now:
                # Already passed today, schedule for tomorrow
                next_run = next_run + timedelta(days=1)
        
        elif schedule.frequency == 'weekly':
            # Find next occurrence of day_of_week at execution_time
            current_weekday = now.weekday()
            target_weekday = schedule.day_of_week
            
            # Calculate days until target weekday
            days_ahead = target_weekday - current_weekday
            
            if days_ahead < 0:
                # Target day already passed this week
                days_ahead += 7
            elif days_ahead == 0:
                # Target day is today, check if time has passed
                next_run = make_datetime(now.date(), execution_time)
                if next_run <= now:
                    # Time already passed, schedule for next week
                    days_ahead = 7
            
            next_run = make_datetime(
                now.date() + timedelta(days=days_ahead),
                execution_time
            )
        
        elif schedule.frequency == 'monthly':
            # Find next occurrence of day_of_month at execution_time
            target_day = schedule.day_of_month
            
            # Try current month first
            try:
                next_run = make_datetime(
                    datetime(now.year, now.month, target_day).date(),
                    execution_time
                )
                
                if next_run <= now:
                    # Already passed this month, try next month
                    if now.month == 12:
                        next_month = 1
                        next_year = now.year + 1
                    else:
                        next_month = now.month + 1
                        next_year = now.year
                    
                    next_run = make_datetime(
                        datetime(next_year, next_month, target_day).date(),
                        execution_time
                    )
            except ValueError:
                # Day doesn't exist in current month, try next month
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                
                next_run = make_datetime(
                    datetime(next_year, next_month, target_day).date(),
                    execution_time
                )
        
        else:
            # Default to tomorrow if frequency is unknown
            next_run = now + timedelta(days=1)
        
        self.logger.info(f"Calculated next run time: {next_run}")
        return next_run
