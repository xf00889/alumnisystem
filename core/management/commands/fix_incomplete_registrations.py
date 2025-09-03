from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix users with incomplete registrations that might be causing login issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--mark-complete',
            action='store_true',
            help='Mark all existing profiles as registration complete',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Checking Registration Status ==='))
        
        # Get all users and their profiles
        users_without_profiles = []
        incomplete_registrations = []
        complete_registrations = []
        
        for user in User.objects.all():
            try:
                profile = user.profile
                if profile.has_completed_registration:
                    complete_registrations.append(user)
                else:
                    incomplete_registrations.append(user)
            except Profile.DoesNotExist:
                users_without_profiles.append(user)
        
        # Report statistics
        self.stdout.write(f"Total users: {User.objects.count()}")
        self.stdout.write(f"Users without profiles: {len(users_without_profiles)}")
        self.stdout.write(f"Users with incomplete registration: {len(incomplete_registrations)}")
        self.stdout.write(f"Users with complete registration: {len(complete_registrations)}")
        
        # Show users without profiles
        if users_without_profiles:
            self.stdout.write(self.style.WARNING('\nUsers without profiles:'))
            for user in users_without_profiles:
                self.stdout.write(f"  - {user.username} ({user.email})")
        
        # Show users with incomplete registration
        if incomplete_registrations:
            self.stdout.write(self.style.WARNING('\nUsers with incomplete registration:'))
            for user in incomplete_registrations:
                self.stdout.write(f"  - {user.username} ({user.email})")
        
        # Handle dry run
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('\n[DRY RUN] No changes made.'))
            return
        
        # Create profiles for users without them
        if users_without_profiles:
            self.stdout.write(self.style.SUCCESS('\nCreating profiles for users without them...'))
            for user in users_without_profiles:
                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    self.stdout.write(f"  ✓ Created profile for {user.username}")
        
        # Mark registrations as complete if requested
        if options['mark_complete'] and incomplete_registrations:
            self.stdout.write(self.style.SUCCESS('\nMarking incomplete registrations as complete...'))
            for user in incomplete_registrations:
                user.profile.has_completed_registration = True
                user.profile.save()
                self.stdout.write(f"  ✓ Marked {user.username} registration as complete")
        
        self.stdout.write(self.style.SUCCESS('\n=== Operation Complete ==='))