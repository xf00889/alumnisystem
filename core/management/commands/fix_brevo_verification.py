#!/usr/bin/env python
"""
Management command to fix Brevo configuration verification status
"""
from django.core.management.base import BaseCommand
from core.models.brevo_config import BrevoConfig
from core.models.email_provider import EmailProvider

class Command(BaseCommand):
    help = 'Fix Brevo configuration verification status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Brevo API key to set',
        )
        parser.add_argument(
            '--from-email',
            type=str,
            help='From email address to set',
        )
        parser.add_argument(
            '--from-name',
            type=str,
            default='NORSU Alumni System',
            help='From name to set',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== FIXING BREVO CONFIGURATION ===")
        
        # Get the active Brevo config
        brevo_config = BrevoConfig.objects.filter(is_active=True).first()
        
        if not brevo_config:
            self.stdout.write(self.style.ERROR("No active Brevo configuration found"))
            return
        
        self.stdout.write(f"Found Brevo config: {brevo_config.name}")
        self.stdout.write(f"Current API key: {brevo_config.api_key[:10]}...")
        self.stdout.write(f"Current from_email: {brevo_config.from_email}")
        self.stdout.write(f"Current is_verified: {brevo_config.is_verified}")
        
        # Update API key if provided
        if options['api_key']:
            brevo_config.api_key = options['api_key']
            self.stdout.write("✓ Updated API key")
        
        # Update from_email if provided
        if options['from_email']:
            brevo_config.from_email = options['from_email']
            self.stdout.write("✓ Updated from_email")
        
        # Update from_name if provided
        if options['from_name']:
            brevo_config.from_name = options['from_name']
            self.stdout.write("✓ Updated from_name")
        
        # Set as verified
        brevo_config.is_verified = True
        brevo_config.save()
        
        self.stdout.write("✓ Set is_verified = True")
        
        # Verify EmailProvider is active
        email_provider = EmailProvider.objects.filter(provider_type='brevo').first()
        if email_provider:
            email_provider.is_active = True
            email_provider.save()
            self.stdout.write("✓ Activated Brevo email provider")
        
        self.stdout.write(self.style.SUCCESS("✓ Brevo configuration fixed successfully!"))
        self.stdout.write(f"Final status: API key={brevo_config.api_key[:10]}..., Email={brevo_config.from_email}, Verified={brevo_config.is_verified}")
