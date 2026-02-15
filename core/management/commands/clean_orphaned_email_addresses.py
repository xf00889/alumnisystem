"""
Management command to clean orphaned email addresses
"""
from django.core.management.base import BaseCommand
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean orphaned email addresses that reference non-existent users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Cleaning orphaned email addresses...'))
        
        # Find email addresses with non-existent users
        orphaned_emails = []
        for email_address in EmailAddress.objects.all():
            try:
                # Try to access the user
                _ = email_address.user
            except User.DoesNotExist:
                orphaned_emails.append(email_address)
        
        if not orphaned_emails:
            self.stdout.write(self.style.SUCCESS('No orphaned email addresses found!'))
            return
        
        self.stdout.write(f'Found {len(orphaned_emails)} orphaned email address(es):')
        
        for email_address in orphaned_emails:
            self.stdout.write(f'  - {email_address.email} (User ID: {email_address.user_id})')
            
            # Delete the email address
            email_address.delete()
            self.stdout.write(self.style.SUCCESS(f'    ✓ Deleted orphaned email address'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Cleanup complete! Removed {len(orphaned_emails)} orphaned email address(es)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
