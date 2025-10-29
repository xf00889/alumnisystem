#!/usr/bin/env python
"""
Management command to debug email configuration
"""
from django.core.management.base import BaseCommand
from core.models.brevo_config import BrevoConfig
from core.models.email_provider import EmailProvider
from core.email_utils import get_active_email_provider
from core.brevo_email import get_brevo_settings

class Command(BaseCommand):
    help = 'Debug email configuration'

    def handle(self, *args, **options):
        self.stdout.write("=== EMAIL CONFIGURATION DEBUG ===")
        
        # Check EmailProvider
        self.stdout.write("\n1. EmailProvider records:")
        providers = EmailProvider.objects.all()
        for p in providers:
            self.stdout.write(f"   ID: {p.id}, Type: {p.provider_type}, Active: {p.is_active}")
        
        active_provider = EmailProvider.get_active_provider()
        if active_provider:
            self.stdout.write(f"   Active Provider: {active_provider.provider_type}")
        else:
            self.stdout.write("   No active provider found")
        
        # Check BrevoConfig
        self.stdout.write("\n2. BrevoConfig records:")
        brevo_configs = BrevoConfig.objects.all()
        for b in brevo_configs:
            self.stdout.write(f"   ID: {b.id}, Active: {b.is_active}, Verified: {b.is_verified}, Email: {b.from_email}")
        
        # Check get_active_email_provider
        self.stdout.write("\n3. get_active_email_provider():")
        provider = get_active_email_provider()
        if provider:
            self.stdout.write(f"   Returns: {provider.provider_type}")
        else:
            self.stdout.write("   Returns: None")
        
        # Check get_brevo_settings
        self.stdout.write("\n4. get_brevo_settings():")
        settings = get_brevo_settings()
        self.stdout.write(f"   API Key: {settings.get('api_key', 'NOT SET')[:10]}...")
        self.stdout.write(f"   From Email: {settings.get('from_email', 'NOT SET')}")
        self.stdout.write(f"   From Name: {settings.get('from_name', 'NOT SET')}")
        
        # Check what the test function would find
        self.stdout.write("\n5. Test function query:")
        test_config = BrevoConfig.objects.filter(is_active=True).first()
        if test_config:
            self.stdout.write(f"   Found: ID {test_config.id}, Verified: {test_config.is_verified}")
        else:
            self.stdout.write("   No active BrevoConfig found")
        
        # Check what email functions would find
        self.stdout.write("\n6. Email function query:")
        email_config = BrevoConfig.objects.filter(is_active=True, is_verified=True).first()
        if email_config:
            self.stdout.write(f"   Found: ID {email_config.id}, Verified: {email_config.is_verified}")
        else:
            self.stdout.write("   No active AND verified BrevoConfig found")
