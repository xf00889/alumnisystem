# Log Cleanup Scheduling - Quick Start Guide

Get automated log cleanup running in 5 minutes.

## Step 1: Configure Retention Policies (2 minutes)

1. Go to Django Admin: `/admin/`
2. Navigate to **Log Viewer > Log Retention Policies**
3. Enable and configure both policies:
   - **Audit Logs**: Enable ✓, Retention: 90 days, Export: CSV
   - **File Logs**: Enable ✓, Retention: 30 days, Export: CSV

## Step 2: Create Cleanup Schedule (1 minute)

1. Navigate to **Log Viewer > Log Cleanup Schedules**
2. Create new schedule:
   - Enable: ✓
   - Frequency: Daily
   - Execution time: 02:00
3. Save

## Step 3: Test Manual Execution (1 minute)

```bash
# Test with dry run
python manage.py cleanup_logs --dry-run

# Test actual cleanup
python manage.py cleanup_logs --manual
```

## Step 4: Set Up Scheduling (1 minute)

### Option A: System Cron (Recommended)

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths):
0 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler >> /path/to/logs/scheduler.log 2>&1

# Save and verify
crontab -l
```

### Option B: Django-Q (Alternative)

```bash
# Install Django-Q
pip install django-q

# Set up scheduled task
python manage.py setup_django_q_schedule --schedule-type hourly

# Start cluster
python manage.py qcluster
```

## Step 5: Verify (30 seconds)

```bash
# Check schedule info
python manage.py run_log_scheduler --info

# Run scheduler once
python manage.py run_log_scheduler
```

## Done! 🎉

Your log cleanup is now automated. Monitor it at:
- **Dashboard**: `/log-viewer/management/`
- **Operation History**: Django Admin > Log Viewer > Log Operation Histories

## Common Schedules

```bash
# Every hour (recommended)
0 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler

# Every 30 minutes
*/30 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler

# Daily at 2 AM
0 2 * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_log_scheduler
```

## Troubleshooting

**Scheduler not running?**
```bash
python manage.py run_log_scheduler --info
```

**Cleanup not executing?**
- Check retention policies are enabled
- Verify schedule is enabled
- Check next_run time in admin

**Permission errors?**
```bash
chmod 755 media/logs/archives
chown www-data:www-data media/logs/archives
```

## Next Steps

- Review operation history after first run
- Adjust retention periods if needed
- Set up monitoring/alerts
- Read full documentation: `SCHEDULING_SETUP.md`

## Support

- Full setup guide: `SCHEDULING_SETUP.md`
- Deployment guide: `DEPLOYMENT_GUIDE.md`
- Cron examples: `cron_examples.txt`
