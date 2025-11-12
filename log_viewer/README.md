# Log Viewer App

A custom Django app for viewing and managing system logs through a web interface with automated cleanup and archival.

## Features

### Log Viewing
- ✅ View system logs in a beautiful, user-friendly interface
- ✅ Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ Filter logs by application/module
- ✅ Search logs by message content
- ✅ Filter logs by date range
- ✅ Export logs to CSV
- ✅ Statistics dashboard showing log counts by level
- ✅ Responsive design matching the alumni_list.html style

### Automated Log Management
- ✅ Configurable retention policies for audit and file logs
- ✅ Scheduled automatic cleanup and archival
- ✅ Export to CSV and PDF before deletion
- ✅ Storage limit management with warnings
- ✅ Operation history tracking
- ✅ Manual cleanup trigger
- ✅ Admin notifications for operations

## Installation

The app is already added to `INSTALLED_APPS` in `settings.py` and URL patterns are configured.

## Access

The log viewer is accessible at: `/admin/logs/`

**Note:** Only staff members and superusers can access the log viewer.

## Usage

1. Navigate to `/admin/logs/` in your browser
2. Select a log file from the dropdown
3. Apply filters:
   - **Log Level**: Filter by severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - **Application**: Filter by Django app/module
   - **Search**: Search for specific text in log messages
   - **Date Range**: Filter logs by date
4. Click "Filter" to apply filters
5. Use "Export" to download filtered logs as CSV
6. Use "Clear" to remove all filters

## Log Files

The app looks for log files in the `logs/` directory:

- `alumni_system.log` - General application logs
- `errors.log` - Error-level logs only

These files are created automatically when logging is configured in `settings.py`.

## Configuration

To enable file-based logging, update `settings.py` with the enhanced logging configuration from `LOGGING_ANALYSIS.md`.

## Automated Log Management

The log viewer includes a comprehensive automated log management system that handles cleanup and archival of both audit logs (database) and file logs (filesystem).

### Quick Start

1. **Configure retention policies** in Django Admin > Log Viewer > Log Retention Policies
2. **Create cleanup schedule** in Django Admin > Log Viewer > Log Cleanup Schedules
3. **Set up scheduling** using cron or Django-Q
4. **Monitor operations** in the Log Management Dashboard

See `SCHEDULING_QUICK_START.md` for a 5-minute setup guide.

### Management Commands

```bash
# Run scheduled cleanup check
python manage.py run_log_scheduler

# Check schedule information
python manage.py run_log_scheduler --info

# Manual cleanup
python manage.py cleanup_logs --manual

# Dry run (test without changes)
python manage.py cleanup_logs --dry-run
```

### Scheduling Options

**System Cron (Recommended for production):**
```bash
# Edit crontab
crontab -e

# Add hourly check
0 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler
```

**Django-Q (Alternative):**
```bash
pip install django-q
python manage.py setup_django_q_schedule --schedule-type hourly
python manage.py qcluster
```

### Documentation

- **Quick Start**: `SCHEDULING_QUICK_START.md` - Get started in 5 minutes
- **Full Setup Guide**: `SCHEDULING_SETUP.md` - Detailed scheduling configuration
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- **Cron Examples**: `cron_examples.txt` - Ready-to-use cron configurations

### Dashboard

Access the Log Management Dashboard at `/log-viewer/management/` (staff only) to:
- View retention policy status
- Check next scheduled run
- Monitor storage usage
- View recent operations
- Manually trigger cleanup

## Future Enhancements

- [ ] Real-time log streaming
- [ ] Log detail view
- [ ] Advanced search with regex
- [ ] Log statistics and analytics
- [ ] Email alerts for critical errors
- [ ] Archive compression
- [ ] Remote archive storage (S3, etc.)

