"""
Management command to set up Django-Q scheduled task for log cleanup.

This command creates a scheduled task in Django-Q for automated log cleanup.
Requires Django-Q to be installed and configured.

Usage:
    python manage.py setup_django_q_schedule
    python manage.py setup_django_q_schedule --schedule-type daily --time "02:00"
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import time as datetime_time


class Command(BaseCommand):
    help = 'Set up Django-Q scheduled task for log cleanup'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--schedule-type',
            type=str,
            default='hourly',
            choices=['hourly', 'daily', 'weekly', 'monthly'],
            help='Schedule type (default: hourly)'
        )
        parser.add_argument(
            '--time',
            type=str,
            default='02:00',
            help='Time to run (HH:MM format, for daily/weekly/monthly, default: 02:00)'
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove existing log cleanup schedule'
        )
    
    def handle(self, *args, **options):
        # Check if Django-Q is installed
        try:
            from django_q.models import Schedule
        except ImportError:
            raise CommandError(
                'Django-Q is not installed. Install it with: pip install django-q\n'
                'See log_viewer/SCHEDULING_SETUP.md for setup instructions.'
            )
        
        # Remove existing schedule if requested
        if options['remove']:
            self.remove_schedule(Schedule)
            return
        
        # Create or update schedule
        self.create_schedule(Schedule, options)
    
    def remove_schedule(self, Schedule):
        """Remove existing log cleanup schedule"""
        deleted_count = Schedule.objects.filter(
            name='Log Cleanup Scheduler'
        ).delete()[0]
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Removed {deleted_count} existing log cleanup schedule(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('○ No existing log cleanup schedule found')
            )
    
    def create_schedule(self, Schedule, options):
        """Create or update Django-Q schedule"""
        schedule_type = options['schedule_type'].upper()
        time_str = options['time']
        
        # Parse time
        try:
            hour, minute = map(int, time_str.split(':'))
            schedule_time = datetime_time(hour, minute)
        except (ValueError, AttributeError):
            raise CommandError(
                f'Invalid time format: {time_str}. Use HH:MM format (e.g., 02:00)'
            )
        
        # Map schedule type to Django-Q constants
        schedule_type_map = {
            'HOURLY': Schedule.HOURLY,
            'DAILY': Schedule.DAILY,
            'WEEKLY': Schedule.WEEKLY,
            'MONTHLY': Schedule.MONTHLY,
        }
        
        # Remove existing schedule
        Schedule.objects.filter(name='Log Cleanup Scheduler').delete()
        
        # Create new schedule
        schedule_kwargs = {
            'func': 'log_viewer.scheduler.LogCleanupScheduler.check_and_execute',
            'name': 'Log Cleanup Scheduler',
            'schedule_type': schedule_type_map[schedule_type],
            'repeats': -1,  # Repeat indefinitely
        }
        
        # Add time for non-hourly schedules
        if schedule_type != 'HOURLY':
            schedule_kwargs['next_run'] = timezone.now().replace(
                hour=schedule_time.hour,
                minute=schedule_time.minute,
                second=0,
                microsecond=0
            )
        
        schedule = Schedule.objects.create(**schedule_kwargs)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created Django-Q scheduled task\n\n'
                f'Schedule ID: {schedule.id}\n'
                f'Function: {schedule.func}\n'
                f'Schedule type: {schedule.get_schedule_type_display()}\n'
                f'Repeats: Indefinitely\n'
            )
        )
        
        if schedule_type != 'HOURLY':
            self.stdout.write(f'Time: {schedule_time.strftime("%H:%M")}\n')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nNext steps:\n'
                f'1. Ensure Django-Q cluster is running: python manage.py qcluster\n'
                f'2. Monitor scheduled tasks in Django Admin > Django Q > Scheduled tasks\n'
                f'3. Check execution in Django Admin > Django Q > Successful tasks\n'
                f'4. View log cleanup history in Log Management Dashboard'
            )
        )
        
        # Check if qcluster is running
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠ Important: Django-Q cluster must be running for scheduled tasks to execute.\n'
                f'Start it with: python manage.py qcluster'
            )
        )
