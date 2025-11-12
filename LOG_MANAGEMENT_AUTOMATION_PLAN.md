# Automated Log Management System - Implementation Plan

## Overview
This document outlines the plan to implement an automated log management system that will:
1. Remove manual "Clear Logs" buttons
2. Automatically archive and export logs on a schedule
3. Auto-delete old logs based on retention policies
4. Export logs as PDF/CSV files before deletion

## Current State Analysis

### Existing Components
1. **Audit Logs (Database)**
   - Model: `AuditLog` in `log_viewer/models.py`
   - Stores: CREATE, UPDATE, DELETE, VIEW operations
   - Fields: action, model_name, user, timestamp, old_values, new_values, etc.
   - Current size: Grows indefinitely

2. **File-Based Logs**
   - Location: `logs/alumni_system.log`, `logs/errors.log`
   - Format: Text files with structured log entries
   - Current size: Grows indefinitely

3. **Current Views**
   - `log_list` - View file-based logs
   - `audit_log_list` - View audit logs
   - `log_export` - Export file logs to CSV
   - `log_clear` - Manual clear function (to be removed)

### Issues with Current System
- ❌ No automatic cleanup
- ❌ Logs grow indefinitely
- ❌ Manual intervention required
- ❌ No archival strategy
- ❌ Risk of disk space issues
- ❌ No compliance with data retention policies

## Proposed Solution

### 1. Automated Log Retention Policy

#### Configuration (settings.py)
```python
# Log Management Settings
LOG_MANAGEMENT = {
    # Retention periods (in days)
    'AUDIT_LOG_RETENTION_DAYS': 90,  # Keep audit logs for 90 days
    'FILE_LOG_RETENTION_DAYS': 30,   # Keep file logs for 30 days
    'ARCHIVE_RETENTION_DAYS': 365,   # Keep archives for 1 year
    
    # Archive settings
    'AUTO_ARCHIVE_ENABLED': True,
    'ARCHIVE_FORMAT': 'pdf',  # 'pdf', 'csv', or 'both'
    'ARCHIVE_LOCATION': 'logs/archives/',
    
    # Cleanup schedule
    'CLEANUP_SCHEDULE': 'daily',  # 'daily', 'weekly', 'monthly'
    'CLEANUP_TIME': '02:00',  # Run at 2 AM
    
    # Export settings
    'EXPORT_BEFORE_DELETE': True,
    'COMPRESS_ARCHIVES': True,  # Compress to .zip
    
    # Email notifications
    'NOTIFY_ADMINS': True,
    'NOTIFICATION_EMAIL': ['admin@example.com'],
}
```

### 2. Django Management Commands

#### Command 1: Archive Old Logs
**File:** `log_viewer/management/commands/archive_logs.py`

**Purpose:** Export old logs to PDF/CSV before deletion

**Features:**
- Export audit logs to PDF with formatted tables
- Export file logs to CSV
- Compress archives to ZIP
- Store in `logs/archives/` directory
- Generate summary report

**Usage:**
```bash
python manage.py archive_logs --days=90 --format=pdf
python manage.py archive_logs --audit-only
python manage.py archive_logs --file-only
```

#### Command 2: Cleanup Old Logs
**File:** `log_viewer/management/commands/cleanup_logs.py`

**Purpose:** Delete logs older than retention period

**Features:**
- Delete audit logs from database
- Rotate file-based logs
- Keep archives based on archive retention policy
- Generate cleanup report
- Send email notification to admins

**Usage:**
```bash
python manage.py cleanup_logs --dry-run  # Preview what will be deleted
python manage.py cleanup_logs --force    # Actually delete
python manage.py cleanup_logs --audit-only
python manage.py cleanup_logs --file-only
```

#### Command 3: Log Management Status
**File:** `log_viewer/management/commands/log_status.py`

**Purpose:** Show current log statistics and health

**Features:**
- Show total log counts
- Show disk space usage
- Show oldest/newest logs
- Show archive status
- Recommend actions

**Usage:**
```bash
python manage.py log_status
```

### 3. Celery Periodic Tasks (Scheduled Automation)

#### Task 1: Daily Archive Task
**File:** `log_viewer/tasks.py`

```python
from celery import shared_task
from celery.schedules import crontab

@shared_task
def archive_old_logs_task():
    """
    Scheduled task to archive logs daily at 2 AM
    """
    # Call archive management command
    # Export logs older than retention period
    # Compress and store archives
    pass

# Schedule in celerybeat_schedule
app.conf.beat_schedule = {
    'archive-logs-daily': {
        'task': 'log_viewer.tasks.archive_old_logs_task',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

#### Task 2: Weekly Cleanup Task
**File:** `log_viewer/tasks.py`

```python
@shared_task
def cleanup_old_logs_task():
    """
    Scheduled task to cleanup logs weekly
    """
    # Delete logs older than retention period
    # Delete old archives
    # Send notification email
    pass

# Schedule in celerybeat_schedule
app.conf.beat_schedule = {
    'cleanup-logs-weekly': {
        'task': 'log_viewer.tasks.cleanup_old_logs_task',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
    },
}
```

### 4. Archive Export Formats

#### PDF Export (Audit Logs)
**Library:** `reportlab` or `weasyprint`

**Features:**
- Professional formatted tables
- Header with date range and filters
- Summary statistics
- Pagination
- Searchable text

**Structure:**
```
Archive Report - Audit Logs
Date Range: 2024-01-01 to 2024-03-31
Generated: 2024-04-01 02:00:00

Summary:
- Total Operations: 15,234
- Creates: 5,123
- Updates: 8,456
- Deletes: 1,655

[Detailed Table]
Timestamp | Action | User | Model | Details
...
```

#### CSV Export (File Logs)
**Library:** Built-in `csv` module

**Features:**
- Standard CSV format
- All log fields included
- Easy to import into Excel/analysis tools

### 5. Admin Dashboard Integration

#### New Admin Page: Log Management
**URL:** `/admin/log-management/`

**Features:**
- View retention policy settings
- View archive status
- Manually trigger archive/cleanup
- Download archived logs
- View cleanup history
- Configure retention policies (UI)

**Sections:**
1. **Current Status**
   - Total audit logs
   - Total file log size
   - Oldest log date
   - Disk space usage

2. **Retention Policies**
   - Audit log retention: 90 days
   - File log retention: 30 days
   - Archive retention: 365 days

3. **Recent Archives**
   - List of archived files
   - Download links
   - File sizes
   - Date ranges

4. **Cleanup History**
   - Last cleanup date
   - Records deleted
   - Space freed
   - Next scheduled cleanup

5. **Manual Actions**
   - [Archive Now] button
   - [Cleanup Now] button
   - [Download All Archives] button

### 6. Database Schema Updates

#### New Model: LogArchive
**File:** `log_viewer/models.py`

```python
class LogArchive(models.Model):
    """Track archived log files"""
    
    ARCHIVE_TYPE_CHOICES = (
        ('AUDIT', 'Audit Logs'),
        ('FILE', 'File Logs'),
    )
    
    archive_type = models.CharField(max_length=10, choices=ARCHIVE_TYPE_CHOICES)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # in bytes
    format = models.CharField(max_length=10)  # 'pdf', 'csv', 'zip'
    
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    record_count = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    
    is_compressed = models.BooleanField(default=False)
    checksum = models.CharField(max_length=64)  # SHA-256 hash
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['archive_type', 'date_from']),
        ]
```

#### New Model: LogCleanupHistory
**File:** `log_viewer/models.py`

```python
class LogCleanupHistory(models.Model):
    """Track cleanup operations"""
    
    cleanup_type = models.CharField(max_length=10)  # 'AUDIT', 'FILE', 'ARCHIVE'
    records_deleted = models.IntegerField()
    space_freed = models.BigIntegerField()  # in bytes
    
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    
    executed_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-executed_at']
```

### 7. Email Notifications

#### Notification Template
**Subject:** Log Management Report - [Date]

**Content:**
```
Log Management Report
Date: 2024-04-01 02:00:00

ARCHIVE SUMMARY
---------------
✓ Audit logs archived: 5,234 records
✓ File logs archived: 1.2 GB
✓ Archive location: logs/archives/2024-04-01_audit_logs.pdf.zip
✓ Archive size: 45 MB (compressed)

CLEANUP SUMMARY
---------------
✓ Audit logs deleted: 3,456 records (older than 90 days)
✓ File logs rotated: 850 MB freed
✓ Old archives deleted: 2 files (older than 365 days)
✓ Total space freed: 895 MB

CURRENT STATUS
--------------
• Total audit logs: 12,345
• Oldest audit log: 2024-01-15
• File log size: 2.3 GB
• Archive count: 45 files
• Total archive size: 1.8 GB

NEXT SCHEDULED TASKS
--------------------
• Next archive: 2024-04-02 02:00:00
• Next cleanup: 2024-04-07 03:00:00

---
This is an automated message from the Alumni System Log Management.
```

### 8. Implementation Phases

#### Phase 1: Foundation (Week 1)
- [ ] Add LOG_MANAGEMENT settings
- [ ] Create LogArchive and LogCleanupHistory models
- [ ] Run migrations
- [ ] Create archive directory structure

#### Phase 2: Management Commands (Week 2)
- [ ] Implement `archive_logs` command
- [ ] Implement `cleanup_logs` command
- [ ] Implement `log_status` command
- [ ] Test commands manually

#### Phase 3: Export Functionality (Week 3)
- [ ] Implement PDF export for audit logs
- [ ] Implement CSV export for file logs
- [ ] Add compression (ZIP)
- [ ] Add checksum generation

#### Phase 4: Celery Tasks (Week 4)
- [ ] Create Celery tasks
- [ ] Configure Celery Beat schedule
- [ ] Test scheduled execution
- [ ] Monitor task execution

#### Phase 5: Admin Interface (Week 5)
- [ ] Create log management admin page
- [ ] Add manual trigger buttons
- [ ] Add archive download functionality
- [ ] Add configuration UI

#### Phase 6: Notifications (Week 6)
- [ ] Create email templates
- [ ] Implement notification sending
- [ ] Test email delivery
- [ ] Add notification preferences

#### Phase 7: Testing & Deployment (Week 7)
- [ ] Integration testing
- [ ] Performance testing
- [ ] Documentation
- [ ] Deploy to production

### 9. Monitoring & Maintenance

#### Metrics to Track
- Archive success rate
- Cleanup success rate
- Disk space trends
- Log growth rate
- Archive file sizes
- Task execution time

#### Alerts
- Archive failure
- Cleanup failure
- Disk space > 80%
- Task execution time > threshold
- Missing scheduled tasks

### 10. Rollback Plan

If issues occur:
1. Disable Celery tasks
2. Restore from archives if needed
3. Re-enable manual log management
4. Fix issues
5. Re-enable automation

### 11. Security Considerations

- ✅ Only admins can access log management
- ✅ Archives are stored securely
- ✅ Checksums verify archive integrity
- ✅ Audit trail of all cleanup operations
- ✅ Email notifications for transparency
- ✅ Dry-run mode for testing

### 12. Compliance & Legal

- Meets data retention requirements
- Provides audit trail
- Allows for data recovery
- Supports compliance reporting
- Maintains data integrity

## Benefits

1. **Automated** - No manual intervention needed
2. **Reliable** - Scheduled tasks run consistently
3. **Compliant** - Meets retention policies
4. **Efficient** - Frees disk space automatically
5. **Transparent** - Email notifications keep admins informed
6. **Recoverable** - Archives allow data recovery
7. **Scalable** - Handles growing log volumes

## Next Steps

1. Review and approve this plan
2. Set retention policy values
3. Begin Phase 1 implementation
4. Schedule weekly progress reviews
5. Plan production deployment

## Questions to Answer

1. What should the retention periods be?
   - Audit logs: 90 days? 180 days?
   - File logs: 30 days? 60 days?
   - Archives: 1 year? 2 years?

2. What archive format is preferred?
   - PDF (better for viewing)
   - CSV (better for analysis)
   - Both?

3. When should cleanup run?
   - Daily? Weekly? Monthly?
   - What time?

4. Who should receive notifications?
   - All admins?
   - Specific email list?

5. Should we keep the manual export functionality?
   - Yes, for ad-hoc exports
   - Remove after automation is stable?
