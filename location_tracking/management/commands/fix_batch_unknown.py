from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile, Education
from location_tracking.models import LocationData
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix batch unknown issue by ensuring users have proper education records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Starting batch unknown fix...'))
        
        # Get users with active locations
        users_with_locations = User.objects.filter(
            locations__is_active=True
        ).distinct()
        
        total_users = users_with_locations.count()
        fixed_users = 0
        users_without_profile = 0
        users_without_education = 0
        users_without_primary = 0
        users_with_multiple_primary = 0
        
        self.stdout.write(f'Found {total_users} users with active locations')
        
        for user in users_with_locations:
            try:
                # Check if user has a profile
                if not hasattr(user, 'profile'):
                    users_without_profile += 1
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(f'User {user.username} has no profile')
                        )
                    
                    if not dry_run:
                        # Create a profile for the user
                        Profile.objects.create(user=user)
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(f'Created profile for {user.username}')
                            )
                    continue
                
                profile = user.profile
                education_records = profile.education.all()
                
                # Check if user has any education records
                if not education_records.exists():
                    users_without_education += 1
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(f'User {user.username} has no education records')
                        )
                    continue
                
                # Check primary education records
                primary_education = education_records.filter(is_primary=True)
                
                if primary_education.count() == 0:
                    # No primary education set - set the most recent one as primary
                    users_without_primary += 1
                    most_recent = education_records.order_by('-graduation_year').first()
                    
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'User {user.username} has no primary education. '
                                f'Setting {most_recent} as primary'
                            )
                        )
                    
                    if not dry_run:
                        most_recent.is_primary = True
                        most_recent.save()
                        fixed_users += 1
                        
                elif primary_education.count() > 1:
                    # Multiple primary education records - keep only the most recent
                    users_with_multiple_primary += 1
                    most_recent_primary = primary_education.order_by('-graduation_year').first()
                    
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'User {user.username} has multiple primary education records. '
                                f'Keeping only {most_recent_primary}'
                            )
                        )
                    
                    if not dry_run:
                        # Set all to non-primary first
                        primary_education.update(is_primary=False)
                        # Then set the most recent as primary
                        most_recent_primary.is_primary = True
                        most_recent_primary.save()
                        fixed_users += 1
                
                else:
                    # User has exactly one primary education - check if it has graduation_year
                    primary = primary_education.first()
                    if not primary.graduation_year:
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'User {user.username} primary education has no graduation year'
                                )
                            )
                        # Could set a default year or prompt for manual fix
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing user {user.username}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Total users with locations: {total_users}')
        self.stdout.write(f'Users without profile: {users_without_profile}')
        self.stdout.write(f'Users without education: {users_without_education}')
        self.stdout.write(f'Users without primary education: {users_without_primary}')
        self.stdout.write(f'Users with multiple primary education: {users_with_multiple_primary}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would fix {fixed_users} users'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_users} users'))
        
        # Show current batch distribution
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('CURRENT BATCH DISTRIBUTION'))
        self.stdout.write('='*50)
        
        batch_groups = {}
        for user in users_with_locations:
            try:
                if hasattr(user, 'profile'):
                    education = user.profile.education.filter(is_primary=True).first()
                    batch = education.graduation_year if education and education.graduation_year else "Unknown"
                else:
                    batch = "Unknown"
                
                if batch not in batch_groups:
                    batch_groups[batch] = 0
                batch_groups[batch] += 1
            except:
                if "Unknown" not in batch_groups:
                    batch_groups["Unknown"] = 0
                batch_groups["Unknown"] += 1
        
        for batch, count in sorted(batch_groups.items()):
            self.stdout.write(f'Batch {batch}: {count} users')
        
        self.stdout.write('\n' + self.style.SUCCESS('Batch fix completed!'))