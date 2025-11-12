# Migration Signal Conflict Test

## Overview

This test script verifies that the migration signal conflict fix is working correctly. It ensures that Django migrations can run without signal-related errors, specifically checking that the `log_viewer` signal handlers don't attempt to create audit logs before the necessary database tables exist.

## What It Tests

The script verifies three key aspects:

1. **Migration Completion**: Migrations run to completion with exit code 0
2. **No Signal Errors**: No signal-related errors appear in the migration output
3. **Table Accessibility**: The log_viewer_auditlog table is accessible after migrations

## Usage

### Basic Usage

Run the test script from the project root:

```bash
python test_migration_signals.py
```

### What Happens

1. The script backs up your existing database (if using SQLite)
2. Removes the database to simulate a fresh deployment
3. Runs `python manage.py migrate --run-syncdb --verbosity=2`
4. Captures and analyzes the output for signal-related errors
5. Restores your original database

### Expected Output

On success, you should see:

```
============================================================
TEST RESULTS:
------------------------------------------------------------
✓ PASSED: Migrations completed successfully without signal errors

The migration signal conflict has been successfully resolved.
Signal handlers correctly skip execution during migrations.
============================================================
```

### Error Patterns Checked

The script looks for these error patterns in the migration output:

- `log_viewer_auditlog`
- `relation "log_viewer_auditlog" does not exist`
- `no such table: log_viewer_auditlog`
- `Table 'log_viewer_auditlog' doesn't exist`
- `ProgrammingError`
- `OperationalError`
- `DoesNotExist`
- `signal handler`
- `AuditLog`

## Requirements

- Python 3.x
- Django project with migrations
- SQLite or MySQL database (script handles both)

## Safety Features

- **Database Backup**: Automatically backs up your database before testing
- **Automatic Restore**: Restores your original database after the test completes
- **Error Handling**: Gracefully handles interruptions and errors
- **Non-Destructive**: Your original data is preserved

## Interpreting Results

### Test Passed

If the test passes, it means:
- Migrations run without errors
- Signal handlers correctly detect migration context
- Signal handlers skip execution during migrations
- The fix is working as intended

### Test Failed

If the test fails, check:
- The error patterns found in the output
- Whether signal handlers are still trying to access tables during migrations
- The migration detection logic in `log_viewer/signals.py`

## Troubleshooting

### "Could not verify table existence"

This is informational only and doesn't indicate a failure. The critical checks are:
1. Migration exit code = 0
2. No signal-related errors in output

### Database Not Restored

If the script is interrupted, you can manually restore your database:
- Look for `db.sqlite3.backup_migration_test` in your project root
- Rename it back to `db.sqlite3`

### Timeout Errors

If migrations take longer than 120 seconds, the script will timeout. You can:
- Increase the timeout in the script
- Run migrations manually to identify slow operations

## Related Files

- `log_viewer/signals.py` - Contains the signal handlers with migration detection
- `.kiro/specs/fix-migration-signal-conflict/` - Full specification and design documents
- `test_migration_signals.py` - This test script

## Notes

- The script is designed for development/testing environments
- For production deployments, use standard migration procedures
- The test simulates a fresh database migration scenario
- Warnings about deprecated settings or MySQL constraints are expected and don't indicate test failure
