"""
Test script for the log cleanup scheduler.

Run with: python manage.py shell < log_viewer/test_scheduler.py
Or: python manage.py runscript test_scheduler (if django-extensions is installed)
"""

from datetime import time as datetime_time
from django.utils import timezone
from log_viewer.models import LogCleanupSchedule, LogRetentionPolicy
from log_viewer.scheduler import LogCleanupScheduler

print("=" * 70)
print("Testing Log Cleanup Scheduler")
print("=" * 70)

# Test 1: Scheduler instantiation
print("\n[Test 1] Instantiating scheduler...")
try:
    scheduler = LogCleanupScheduler()
    print("✓ Scheduler instantiated successfully")
except Exception as e:
    print(f"✗ Failed to instantiate scheduler: {e}")
    exit(1)

# Test 2: Get next run info with no schedule
print("\n[Test 2] Getting next run info (no schedule)...")
try:
    info = scheduler.get_next_run_info()
    if not info['enabled']:
        print(f"✓ Correctly reports no active schedule: {info['message']}")
    else:
        print("✗ Should report no active schedule")
except Exception as e:
    print(f"✗ Failed to get next run info: {e}")

# Test 3: Create a test schedule
print("\n[Test 3] Creating test schedule...")
try:
    # Clean up any existing schedules
    LogCleanupSchedule.objects.all().delete()
    
    schedule = LogCleanupSchedule.objects.create(
        enabled=True,
        frequency='daily',
        execution_time=datetime_time(2, 0),
    )
    print(f"✓ Created test schedule (ID: {schedule.id})")
    print(f"  Frequency: {schedule.get_frequency_display()}")
    print(f"  Execution time: {schedule.execution_time}")
except Exception as e:
    print(f"✗ Failed to create schedule: {e}")
    exit(1)

# Test 4: Get next run info with schedule
print("\n[Test 4] Getting next run info (with schedule)...")
try:
    info = scheduler.get_next_run_info()
    if info['enabled']:
        print("✓ Schedule is enabled")
        print(f"  Frequency: {info['frequency']}")
        print(f"  Execution time: {info['execution_time']}")
        print(f"  Last run: {info['last_run']}")
        print(f"  Next run: {info['next_run']}")
    else:
        print("✗ Schedule should be enabled")
except Exception as e:
    print(f"✗ Failed to get next run info: {e}")

# Test 5: Check and execute (should initialize next_run)
print("\n[Test 5] Running scheduler check (should initialize)...")
try:
    result = scheduler.check_and_execute()
    if not result['executed'] and result['reason'] == 'Schedule initialized':
        print("✓ Schedule initialized correctly")
        print(f"  Next run: {result.get('next_run')}")
    else:
        print(f"○ Result: {result}")
except Exception as e:
    print(f"✗ Failed to check and execute: {e}")

# Test 6: Verify next_run was calculated
print("\n[Test 6] Verifying next_run calculation...")
try:
    schedule.refresh_from_db()
    if schedule.next_run:
        print(f"✓ Next run calculated: {schedule.next_run}")
        print(f"  Current time: {timezone.now()}")
        if schedule.next_run > timezone.now():
            print("✓ Next run is in the future")
        else:
            print("○ Next run is in the past (cleanup would execute)")
    else:
        print("✗ Next run not calculated")
except Exception as e:
    print(f"✗ Failed to verify next_run: {e}")

# Test 7: Check retention policies
print("\n[Test 7] Checking retention policies...")
try:
    audit_policy = LogRetentionPolicy.objects.filter(log_type='audit').first()
    file_policy = LogRetentionPolicy.objects.filter(log_type='file').first()
    
    if audit_policy:
        print(f"✓ Audit policy exists")
        print(f"  Enabled: {audit_policy.enabled}")
        print(f"  Retention days: {audit_policy.retention_days}")
    else:
        print("○ No audit policy found")
    
    if file_policy:
        print(f"✓ File policy exists")
        print(f"  Enabled: {file_policy.enabled}")
        print(f"  Retention days: {file_policy.retention_days}")
    else:
        print("○ No file policy found")
except Exception as e:
    print(f"✗ Failed to check policies: {e}")

# Test 8: Test scheduler with disabled schedule
print("\n[Test 8] Testing with disabled schedule...")
try:
    schedule.enabled = False
    schedule.save()
    
    result = scheduler.check_and_execute()
    if not result['executed'] and result['reason'] == 'No active schedule configured':
        print("✓ Correctly handles disabled schedule")
    else:
        print(f"○ Result: {result}")
    
    # Re-enable for cleanup
    schedule.enabled = True
    schedule.save()
except Exception as e:
    print(f"✗ Failed to test disabled schedule: {e}")

# Cleanup
print("\n[Cleanup] Removing test schedule...")
try:
    schedule.delete()
    print("✓ Test schedule removed")
except Exception as e:
    print(f"○ Failed to remove test schedule: {e}")

print("\n" + "=" * 70)
print("Scheduler tests completed!")
print("=" * 70)
print("\nTo set up scheduling for production:")
print("1. Configure retention policies in Django Admin")
print("2. Create and enable a cleanup schedule")
print("3. Set up cron or Django-Q (see SCHEDULING_SETUP.md)")
print("4. Run: python manage.py run_log_scheduler --info")
