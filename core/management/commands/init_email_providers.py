"""
Management command to initialize email providers
"""
from django.core.management.base import BaseCommand
from core.models.email_provider import EmailProvider

class Command(BaseCommand):
    help = 'Initialize email providers (SMTP and Brevo)'

    def handle(self, *args, **options):
        # Create SMTP provider if it doesn't exist
        smtp_provider, created = EmailProvider.objects.get_or_create(
            provider_type='smtp',
            defaults={'is_active': True}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Created SMTP email provider')
            )
        else:
            self.stdout.write(
                self.style.WARNING('SMTP email provider already exists')
            )
        
        # Create Brevo provider if it doesn't exist
        brevo_provider, created = EmailProvider.objects.get_or_create(
            provider_type='brevo',
            defaults={'is_active': False}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Created Brevo email provider')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Brevo email provider already exists')
            )
        
        # Show current status
        self.stdout.write('\nCurrent email provider status:')
        for provider in EmailProvider.objects.all():
            status = "Active" if provider.is_active else "Inactive"
            configured = "Configured" if provider.is_configured() else "Not configured"
            self.stdout.write(
                f"  {provider.get_provider_type_display()}: {status} - {configured}"
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nEmail providers initialized successfully!')
        )
