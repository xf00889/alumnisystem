# Log Automation System - Deployment Guide

This guide covers the complete deployment process for the automated log management system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Scheduling Setup](#scheduling-setup)
5. [Testing](#testing)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Django 5.0+
- Python 3.10+
- Database (PostgreSQL/MySQL/SQLite)
- Redis (optional, for Django-Q)
- System access for cron setup (production)

## Installation

### 1. Install Dependencies

The log automation system requires ReportLab for PDF generation:

```bash
pip install reportlab==4.1.0
```

Optional: Install Django-Q for task scheduling:

```bash
pip install django-q==1.3.9
```

### 2. Update requirements.txt

Ensure these packages are in your `requirements.txt`:

```
reportlab==4.1.0
django-q==1.3.9  # Optional
```

### 3. Verify Installation

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Run Migrations

The log automation system includes several models that need to be migrated:

```bash
python manage.py migrate log_viewer
```

This creates:
- `LogRetentionPolicy` - Retention policy configuration
- `LogCleanupSchedule` - Cleanup schedule configuration
- `LogOperationHistory` - Operation history tracking
- `ArchiveStorageConfig` - Storage management configuration

### 2. Create Default Configurations

Default configurations are created automatically via data migration:

- Audit log retention: 90 days (disabled by default)
- File log retention: 30 days (disabled by default)
- Archive storage limit: 10 GB

### 3. Configure Retention Policies

1. Access Django Admin: `/admin/`
2. Navigate to **Log Viewer > Log Retention Policies**
3. Configure policies for each log type:

   **Audit Logs:**
   - Enable: ✓
   - Retention days: 90 (adjust as needed)
   - Export before delete: ✓
   - Export format: CSV or PDF or Both
   - Archive path: `logs/archives` (default)

   **File Logs:**
   - Enable: ✓
   - Retention days: 30 (adjust as needed)
   - Export before delete: ✓
   - Export format: CSV or PDF or Both
   - Archive path: `logs/archives` (default)

4. Save changes

### 4. Configure Cleanup Schedule

1. Navigate to **Log Viewer > Log Cleanup Schedules**
2. Create a new schedule or edit existing:
   - Enable: ✓
   - Frequency: Daily (or Weekly/Monthly)
   - Execution time: 02:00 (2 AM recommended)
   - Day of week: (for weekly schedules)
   - Day of month: (for monthly schedules, 1-28)

3. Save changes

### 5. Configure Archive Storage

1. Navigate to **Log Viewer > Archive Storage Configs**
2. Configure storage limits:
   - Max storage GB: 10 (adjust based on available space)
   - Warning threshold: 80%
   - Critical threshold: 95%

3. Save changes

### 6. Create Archive Directory

Ensure the archive directory exists and is writable:

```bash
mkdir -p media/logs/archives
chmod 755 media/logs/archives
```

For production, ensure the web server user has write access:

```bash
chown -R www-data:www-data media/logs/archives
```

## Scheduling Setup

Choose one of the following scheduling methods based on your environment.

### Option A: System Cron (Recommended for Production)

#### Linux/Unix Setup

1. **Edit crontab:**
   ```bash
   crontab -e
   ```

2. **Add entry for hourly checks:**
   ```cron
   0 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler >> /path/to/logs/scheduler.log 2>&1
   ```

3. **Example with full paths:**
   ```cron
   0 * * * * cd /var/www/alumni_system && /var/www/alumni_system/venv/bin/python manage.py run_log_scheduler >> /var/www/alumni_system/logs/scheduler.log 2>&1
   ```

4. **Verify:**
   ```bash
   crontab -l
   ```

#### Windows Setup

1. Open **Task Scheduler**
2. Create new task:
   - Name: "Alumni System Log Cleanup"
   - Trigger: Daily at 2:00 AM
   - Action: Start a program
     - Program: `C:\path\to\venv\Scripts\python.exe`
     - Arguments: `manage.py run_log_scheduler`
     - Start in: `C:\path\to\project`

#### Render.com Setup

Add to `render.yaml`:

```yaml
services:
  - type: cron
    name: log-cleanup-scheduler
    env: python
    schedule: "0 * * * *"  # Every hour
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python manage.py run_log_scheduler"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: alumni-db
          property: connectionString
      - key: SECRET_KEY
        sync: false
```

### Option B: Django-Q (Alternative)

#### 1. Configure Django-Q

Add to `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps ...
    'django_q',
]

Q_CLUSTER = {
    'name': 'alumni_system',
    'workers': 2,
    'recycle': 500,
    'timeout': 300,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': {
        'host': config('REDIS_HOST', default='127.0.0.1'),
        'port': config('REDIS_PORT', default=6379, cast=int),
        'db': config('REDIS_DB', default=0, cast=int),
    }
}
```

#### 2. Run Migrations

```bash
python manage.py migrate
```

#### 3. Create Scheduled Task

```bash
python manage.py setup_django_q_schedule --schedule-type hourly
```

#### 4. Start Django-Q Cluster

Development:
```bash
python manage.py qcluster
```

Production (systemd service):
```bash
sudo systemctl enable django-q
sudo systemctl start django-q
```

See `SCHEDULING_SETUP.md` for detailed Django-Q setup.

## Testing

### 1. Test Manual Cleanup

```bash
# Dry run (no changes)
python manage.py cleanup_logs --dry-run

# Actual cleanup
python manage.py cleanup_logs --manual
```

### 2. Test Scheduler

```bash
# Check schedule info
python manage.py run_log_scheduler --info

# Run scheduler once
python manage.py run_log_scheduler
```

### 3. Verify in Admin

1. Check **Log Operation Histories** for execution records
2. Verify archives were created in `media/logs/archives/`
3. Check that old logs were deleted

### 4. Test Continuous Mode (Development)

```bash
python manage.py run_log_scheduler --continuous --interval 60
```

Press Ctrl+C to stop.

## Monitoring

### 1. Operation History

Monitor cleanup operations in Django Admin:
- Navigate to **Log Viewer > Log Operation Histories**
- Filter by status, operation type, date range
- Export history to CSV for analysis

### 2. Log Management Dashboard

Access the dashboard at `/log-viewer/management/` (staff only):
- View retention policies status
- Check next scheduled run
- Monitor storage usage
- View recent operations
- Manually trigger cleanup

### 3. Scheduler Logs

Monitor scheduler execution:

```bash
# If using cron
tail -f /path/to/logs/scheduler.log

# If using Django-Q
python manage.py qmonitor
```

### 4. Storage Monitoring

Check archive storage usage:
- Django Admin > Log Viewer > Archive Storage Configs
- Dashboard shows storage usage with progress bar
- Warnings at 80%, critical at 95%

### 5. Notifications

Configure admin notifications for:
- Successful cleanup operations
- Failed operations (high priority)
- Storage warnings (80% threshold)
- Storage critical (95% threshold)

## Troubleshooting

### Cleanup Not Running

**Check schedule is enabled:**
```bash
python manage.py run_log_scheduler --info
```

**Verify retention policies:**
- Django Admin > Log Viewer > Log Retention Policies
- Ensure at least one policy is enabled

**Check next_run time:**
- Django Admin > Log Viewer > Log Cleanup Schedules
- Verify next_run is calculated correctly

### Permission Errors

**Archive directory:**
```bash
ls -la media/logs/
chmod 755 media/logs/archives
chown www-data:www-data media/logs/archives
```

**Log files:**
```bash
ls -la logs/
chmod 644 logs/*.log
chown www-data:www-data logs/*.log
```

### Export Failures

**Check ReportLab installation:**
```bash
python -c "import reportlab; print(reportlab.Version)"
```

**Verify archive path:**
- Check path exists and is writable
- Check disk space: `df -h`

### Cron Not Running

**Check cron service:**
```bash
sudo service cron status
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog
```

**Test command manually:**
```bash
cd /path/to/project
/path/to/venv/bin/python manage.py run_log_scheduler
```

### Django-Q Issues

**Check cluster is running:**
```bash
python manage.py qmonitor
```

**Check scheduled tasks:**
- Django Admin > Django Q > Scheduled tasks
- Verify task exists and is enabled

**Check failed tasks:**
- Django Admin > Django Q > Failed tasks
- Review error messages

## Production Checklist

- [ ] Dependencies installed (reportlab)
- [ ] Migrations run
- [ ] Retention policies configured and enabled
- [ ] Cleanup schedule created and enabled
- [ ] Archive directory created and writable
- [ ] Storage limits configured
- [ ] Scheduling method chosen and configured
- [ ] Manual cleanup tested successfully
- [ ] Scheduler tested (dry run)
- [ ] First scheduled execution verified
- [ ] Operation history being recorded
- [ ] Archives being created correctly
- [ ] Old logs being deleted
- [ ] Notifications configured (if desired)
- [ ] Monitoring set up
- [ ] Documentation updated for team
- [ ] Backup strategy in place

## Maintenance

### Regular Tasks

**Weekly:**
- Review operation history for failures
- Check storage usage
- Verify archives are being created

**Monthly:**
- Review retention policies
- Adjust if needed based on usage
- Clean up old archives if needed
- Review storage limits

**Quarterly:**
- Audit log cleanup effectiveness
- Review and optimize retention periods
- Update documentation

### Backup Strategy

**Archive backups:**
- Archives are already exports of logs
- Consider backing up archives to external storage
- Implement archive rotation if needed

**Configuration backups:**
- Export retention policies configuration
- Document schedule settings
- Keep copy of cron entries

## Support and Documentation

**Additional Documentation:**
- `SCHEDULING_SETUP.md` - Detailed scheduling setup guide
- `log_viewer/README.md` - Log viewer app documentation

**Management Commands:**
- `cleanup_logs` - Execute log cleanup
- `run_log_scheduler` - Run scheduler check
- `setup_django_q_schedule` - Set up Django-Q task

**Admin Interfaces:**
- Log Retention Policies
- Log Cleanup Schedules
- Log Operation Histories
- Archive Storage Configs

## Security Considerations

1. **Access Control:**
   - Only superusers can configure policies
   - Only staff can view operation history
   - Manual trigger requires staff permission

2. **Archive Protection:**
   - Archives stored outside web-accessible directory
   - Proper file permissions (600 for sensitive logs)
   - Consider encryption for sensitive data

3. **Audit Trail:**
   - All operations logged in operation history
   - Manual operations record triggering user
   - Configuration changes tracked

## Performance Optimization

1. **Batch Processing:**
   - Logs processed in batches of 1000 records
   - Prevents memory issues with large datasets

2. **Database Optimization:**
   - Index on AuditLog.timestamp
   - Use bulk operations for deletion

3. **File Processing:**
   - Stream large log files
   - Process line by line for memory efficiency

4. **Scheduling:**
   - Run during off-peak hours (2-4 AM recommended)
   - Adjust frequency based on log volume

## Rollback Procedure

If issues occur after deployment:

1. **Disable scheduling:**
   - Django Admin > Log Cleanup Schedules
   - Uncheck "Enabled"

2. **Disable retention policies:**
   - Django Admin > Log Retention Policies
   - Uncheck "Enabled" for all policies

3. **Stop scheduler:**
   ```bash
   # If using cron
   crontab -e  # Comment out the entry
   
   # If using Django-Q
   python manage.py setup_django_q_schedule --remove
   ```

4. **Restore from backup if needed:**
   - Restore database backup
   - Restore log files from backup

## Upgrade Path

When upgrading the log automation system:

1. Backup current configuration
2. Run new migrations
3. Test in staging environment
4. Update cron entries if needed
5. Monitor first few executions
6. Update documentation

## Contact and Support

For issues or questions:
1. Check operation history in Django Admin
2. Review scheduler logs
3. Test manual execution
4. Verify configuration settings
5. Consult this documentation
