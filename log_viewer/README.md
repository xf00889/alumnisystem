# Log Viewer App

A custom Django app for viewing and managing system logs through a web interface.

## Features

- ✅ View system logs in a beautiful, user-friendly interface
- ✅ Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ Filter logs by application/module
- ✅ Search logs by message content
- ✅ Filter logs by date range
- ✅ Export logs to CSV
- ✅ Statistics dashboard showing log counts by level
- ✅ Responsive design matching the alumni_list.html style

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

## Future Enhancements

- [ ] Real-time log streaming
- [ ] Log detail view
- [ ] Log clearing functionality
- [ ] Log archiving
- [ ] Advanced search with regex
- [ ] Log statistics and analytics
- [ ] Email alerts for critical errors

