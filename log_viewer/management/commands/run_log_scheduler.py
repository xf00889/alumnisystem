"""
Management command to run the log cleanup scheduler.

This command checks if cleanup is due and executes it if necessary.
Can be run via cron or as a periodic task.

Usage:
    python manage.py run_log_scheduler
    python manage.py run_log_scheduler --continuous --interval 3600
"""

from django.core.management.base import BaseCommand
import time
import logging

from log_viewer.scheduler import LogCleanupScheduler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the log cleanup scheduler to check and execute scheduled cleanups'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously in a loop (for development/testing)'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,
            help='Check interval in seconds when running continuously (default: 3600)'
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Display next run information and exit'
        )
    
    def handle(self, *args, **options):
        scheduler = LogCleanupScheduler()
        
        # If --info flag, just display schedule info
        if options['info']:
            self.display_schedule_info(scheduler)
            return
        
        # If --continuous flag, run in a loop
        if options['continuous']:
            self.run_continuous(scheduler, options['interval'])
        else:
            # Single execution
            self.run_once(scheduler)
    
    def run_once(self, scheduler):
        """Execute scheduler once and exit"""
        self.stdout.write(self.style.SUCCESS('Checking for scheduled cleanup...'))
        
        result = scheduler.check_and_execute()
        
        if result.get('executed'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Cleanup executed successfully\n"
                    f"  Operation ID: {result['operation_id']}\n"
                    f"  Status: {result['status']}\n"
                    f"  Audit logs processed: {result['metrics']['audit_logs_processed']}\n"
                    f"  Audit logs deleted: {result['metrics']['audit_logs_deleted']}\n"
                    f"  File logs processed: {result['metrics']['file_logs_processed']}\n"
                    f"  File logs deleted: {result['metrics']['file_logs_deleted']}\n"
                    f"  Archives created: {result['metrics']['archives_created']}\n"
                    f"  Next run: {result['next_run']}"
                )
            )
        elif result.get('error'):
            self.stdout.write(
                self.style.ERROR(
                    f"✗ Scheduler error: {result['error']}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"○ Cleanup not executed: {result['reason']}"
                )
            )
            if result.get('next_run'):
                self.stdout.write(f"  Next run: {result['next_run']}")
    
    def run_continuous(self, scheduler, interval):
        """Run scheduler continuously with specified interval"""
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting continuous scheduler (checking every {interval} seconds)\n'
                f'Press Ctrl+C to stop'
            )
        )
        
        try:
            while True:
                result = scheduler.check_and_execute()
                
                if result.get('executed'):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                            f"Cleanup executed (Operation {result['operation_id']})"
                        )
                    )
                elif result.get('error'):
                    self.stdout.write(
                        self.style.ERROR(
                            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                            f"Error: {result['error']}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"{result['reason']}"
                    )
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nScheduler stopped'))
    
    def display_schedule_info(self, scheduler):
        """Display information about the next scheduled run"""
        info = scheduler.get_next_run_info()
        
        if not info['enabled']:
            self.stdout.write(
                self.style.WARNING(
                    f"✗ {info['message']}\n\n"
                    f"To enable scheduling:\n"
                    f"1. Go to Django Admin > Log Viewer > Log Cleanup Schedules\n"
                    f"2. Create or enable a schedule\n"
                    f"3. Configure frequency and execution time"
                )
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Scheduled cleanup is enabled\n\n"
                f"Frequency: {info['frequency']}\n"
                f"Execution time: {info['execution_time']}"
            )
        )
        
        if info['day_of_week']:
            self.stdout.write(f"Day of week: {info['day_of_week']}")
        
        if info['day_of_month']:
            self.stdout.write(f"Day of month: {info['day_of_month']}")
        
        if info['last_run']:
            self.stdout.write(f"\nLast run: {info['last_run']}")
        
        if info['next_run']:
            self.stdout.write(
                self.style.SUCCESS(f"Next run: {info['next_run']}")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Next run: Not calculated yet")
            )
