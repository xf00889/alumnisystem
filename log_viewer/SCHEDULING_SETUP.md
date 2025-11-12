# Log Cleanup Scheduling Setup Guide

This guide explains how to set up automated log cleanup scheduling for the Alumni System. Three approaches are supported:

1. **System Cron** (Recommended for production)
2. **Django-Q** (Recommended for development/small deployments)
3. **Manual Execution** (For testing or on-demand cleanup)

## Prerequisites

Before setting up scheduling, ensure:

1. Log retention policies are configured in Django Admin
2. A cleanup schedule is created and enabled
3. The `cleanup_logs` management command works correctly

Test the cleanup command manually:
```bash
python manage.py cleanup_logs --dry-run
```

## Option 1: System Cron (Production - Recommended)

System cron is the most reliable and lightweight option for production environments.

### Setup on Linux/Unix

1. **Open crontab editor:**
   ```bash
   crontab -e
   ```

2. **Add cron entry:**
   
   For hourly checks:
   ```cron
   0 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler >> /path/to/logs/scheduler.log 2>&1
   ```
   
   For checks every 30 minutes:
   ```cron
   */30 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler >> /path/to/logs/scheduler.log 2>&1
   ```
   
   For daily at 2 AM:
   ```cron
   0 2 * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler >> /path/to/logs/scheduler.log 2>&1
   ```

3. **Example with full paths:**
   ```cron
   0 * * * * cd /var/www/alumni_system && /var/www/alumni_system/venv/bin/python manage.py run_log_scheduler >> /var/www/alumni_system/logs/scheduler.log 2>&1
   ```

4. **Verify cron is running:**
   ```bash
   crontab -l
   ```

### Setup on Windows

1. **Open Task Scheduler**

2. **Create a new task:**
   - Name: "Alumni System Log Cleanup"
   - Trigger: Daily at 2:00 AM (or your preferred schedule)
   - Action: Start a program
     - Program: `C:\path\to\venv\Scripts\python.exe`
     - Arguments: `manage.py run_log_scheduler`
     - Start in: `C:\path\to\project`

3. **Test the task:**
   - Right-click the task and select "Run"
   - Check the logs for execution

### Setup on Render.com (Cloud Platform)

Render supports cron jobs as a separate service:

1. **Add to `render.yaml`:**
   ```yaml
   services:
     - type: web
       name: alumni-system
       # ... existing web service config ...
     
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
         # ... other environment variables ...
   ```

2. **Deploy the updated configuration**

3. **Monitor cron job logs in Render dashboard**

## Option 2: Django-Q (Development/Small Deployments)

Django-Q provides a Django-native task queue with scheduling capabilities.

### Installation

1. **Install Django-Q:**
   ```bash
   pip install django-q
   ```

2. **Update `requirements.txt`:**
   ```
   django-q==1.3.9
   ```

3. **Add to `INSTALLED_APPS` in `settings.py`:**
   ```python
   INSTALLED_APPS = [
       # ... other apps ...
       'django_q',
   ]
   ```

4. **Configure Django-Q in `settings.py`:**
   ```python
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

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

### Create Scheduled Task

1. **Start Django-Q cluster:**
   ```bash
   python manage.py qcluster
   ```

2. **Create scheduled task in Django shell:**
   ```python
   python manage.py shell
   
   from django_q.models import Schedule
   
   # Create hourly schedule
   Schedule.objects.create(
       func='log_viewer.scheduler.LogCleanupScheduler.check_and_execute',
       schedule_type=Schedule.HOURLY,
       name='Log Cleanup Scheduler',
       repeats=-1  # Repeat indefinitely
   )
   ```

3. **Or create via Django Admin:**
   - Go to Django Admin > Django Q > Scheduled tasks
   - Click "Add scheduled task"
   - Function: `log_viewer.scheduler.LogCleanupScheduler.check_and_execute`
   - Schedule type: Hourly (or your preference)
   - Repeats: -1 (infinite)

### Running Django-Q in Production

For production with Django-Q, you need to run the qcluster as a service:

**Systemd service (Linux):**

Create `/etc/systemd/system/django-q.service`:
```ini
[Unit]
Description=Django Q Cluster
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/alumni_system
ExecStart=/var/www/alumni_system/venv/bin/python manage.py qcluster
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable django-q
sudo systemctl start django-q
sudo systemctl status django-q
```

## Option 3: Manual Execution

For testing or on-demand cleanup without scheduling.

### Single Execution

```bash
python manage.py run_log_scheduler
```

### Check Schedule Information

```bash
python manage.py run_log_scheduler --info
```

### Continuous Mode (Development Only)

Run scheduler in a loop for testing:
```bash
python manage.py run_log_scheduler --continuous --interval 60
```

This checks every 60 seconds. Press Ctrl+C to stop.

## Verification and Testing

### 1. Test the Scheduler Command

```bash
# Check schedule info
python manage.py run_log_scheduler --info

# Run once
python manage.py run_log_scheduler

# Dry run the actual cleanup
python manage.py cleanup_logs --dry-run
```

### 2. Verify Schedule Configuration

1. Go to Django Admin > Log Viewer > Log Cleanup Schedules
2. Ensure a schedule is enabled
3. Check that `next_run` is calculated correctly

### 3. Monitor Execution

Check operation history:
1. Django Admin > Log Viewer > Log Operation Histories
2. Or visit the Log Management Dashboard

### 4. Check Logs

Monitor scheduler logs:
```bash
# If using cron
tail -f /path/to/logs/scheduler.log

# If using Django-Q
python manage.py qmonitor
```

## Troubleshooting

### Scheduler Not Running

1. **Check if schedule is enabled:**
   ```bash
   python manage.py run_log_scheduler --info
   ```

2. **Verify cron is running:**
   ```bash
   # Linux
   sudo service cron status
   
   # Check cron logs
   grep CRON /var/log/syslog
   ```

3. **Check Django-Q cluster:**
   ```bash
   python manage.py qmonitor
   ```

### Cleanup Not Executing

1. **Check retention policies are enabled:**
   - Django Admin > Log Viewer > Log Retention Policies

2. **Verify next_run time:**
   - Django Admin > Log Viewer > Log Cleanup Schedules
   - Ensure `next_run` is in the past

3. **Test manual execution:**
   ```bash
   python manage.py cleanup_logs --manual
   ```

### Permission Errors

Ensure the user running the scheduler has:
- Read/write access to log files
- Write access to archive directory
- Database access

### Time Zone Issues

Ensure `USE_TZ = True` in settings.py and schedule times are in the correct timezone.

## Recommended Setup by Environment

### Development
- Use Django-Q with continuous mode or manual execution
- Check interval: Every 5-10 minutes for testing

### Staging
- Use system cron with hourly checks
- Or Django-Q with systemd service

### Production
- **Recommended:** System cron with hourly checks
- Alternative: Django-Q with systemd service and monitoring
- Ensure proper logging and monitoring
- Set up alerts for failed operations

## Configuration Checklist

- [ ] Retention policies configured and enabled
- [ ] Cleanup schedule created and enabled
- [ ] Archive directory exists and is writable
- [ ] Scheduler command tested manually
- [ ] Cron job or Django-Q task created
- [ ] Logs are being written
- [ ] First scheduled execution verified
- [ ] Operation history is being recorded
- [ ] Notifications are working (if enabled)
- [ ] Documentation updated for team

## Next Steps

After setting up scheduling:

1. Monitor the first few scheduled executions
2. Verify archives are being created correctly
3. Check storage usage regularly
4. Adjust retention periods if needed
5. Set up alerts for failed operations
6. Document the setup for your team

## Support

For issues or questions:
1. Check operation history in Django Admin
2. Review scheduler logs
3. Test manual execution
4. Verify configuration settings
