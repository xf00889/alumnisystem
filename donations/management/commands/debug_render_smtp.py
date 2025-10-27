"""
Debug SMTP configuration on Render
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.smtp_settings import get_smtp_settings, update_django_email_settings
from core.models import SMTPConfig
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug SMTP configuration on Render'

    def handle(self, *args, **options):
        self.stdout.write("=== RENDER SMTP DEBUG ===")
        
        # Check Django settings
        self.stdout.write(f"\n1. Django Email Settings:")
        self.stdout.write(f"   DEBUG: {settings.DEBUG}")
        self.stdout.write(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"   EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Check database SMTP config
        self.stdout.write(f"\n2. Database SMTP Configuration:")
        try:
            active_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
            if active_config:
                self.stdout.write(f"   Active Config: {active_config.name}")
                self.stdout.write(f"   Host: {active_config.host}")
                self.stdout.write(f"   Port: {active_config.port}")
                self.stdout.write(f"   TLS: {active_config.use_tls}")
                self.stdout.write(f"   SSL: {active_config.use_ssl}")
                self.stdout.write(f"   Username: {active_config.username}")
                self.stdout.write(f"   From Email: {active_config.from_email}")
                self.stdout.write(f"   Verified: {active_config.is_verified}")
            else:
                self.stdout.write("   No active SMTP configuration found")
        except Exception as e:
            self.stdout.write(f"   Error: {str(e)}")
        
        # Check SMTP settings from database
        self.stdout.write(f"\n3. SMTP Settings from Database:")
        try:
            smtp_settings = get_smtp_settings()
            for key, value in smtp_settings.items():
                if 'password' in key.lower():
                    self.stdout.write(f"   {key}: {'*' * len(str(value)) if value else 'None'}")
                else:
                    self.stdout.write(f"   {key}: {value}")
        except Exception as e:
            self.stdout.write(f"   Error: {str(e)}")
        
        # Test network connectivity
        self.stdout.write(f"\n4. Network Connectivity Test:")
        try:
            import socket
            import smtplib
            
            # Test common SMTP ports
            smtp_servers = [
                ('smtp.gmail.com', 587),
                ('smtp.gmail.com', 465),
                ('smtp-mail.outlook.com', 587),
                ('smtp.mail.yahoo.com', 587),
            ]
            
            for host, port in smtp_servers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        self.stdout.write(f"   ✓ {host}:{port} - Reachable")
                    else:
                        self.stdout.write(f"   ✗ {host}:{port} - Not reachable")
                except Exception as e:
                    self.stdout.write(f"   ✗ {host}:{port} - Error: {str(e)}")
                    
        except Exception as e:
            self.stdout.write(f"   Error testing connectivity: {str(e)}")
        
        # Test email sending with current settings
        self.stdout.write(f"\n5. Email Sending Test:")
        try:
            from django.core.mail import send_mail
            from django.core.mail.backends.console import EmailBackend
            
            # Test with console backend first
            self.stdout.write("   Testing console backend...")
            send_mail(
                'Test Email - Console Backend',
                'This is a test email using console backend.',
                settings.DEFAULT_FROM_EMAIL,
                ['test@example.com'],
                fail_silently=False,
            )
            self.stdout.write("   ✓ Console backend works")
            
            # Test with SMTP backend if available
            if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
                self.stdout.write("   Testing SMTP backend...")
                try:
                    send_mail(
                        'Test Email - SMTP Backend',
                        'This is a test email using SMTP backend.',
                        settings.DEFAULT_FROM_EMAIL,
                        ['test@example.com'],
                        fail_silently=True,
                    )
                    self.stdout.write("   ✓ SMTP backend works")
                except Exception as e:
                    self.stdout.write(f"   ✗ SMTP backend failed: {str(e)}")
            else:
                self.stdout.write("   Using console backend (SMTP not configured)")
                
        except Exception as e:
            self.stdout.write(f"   Error testing email: {str(e)}")
        
        # Check if we're on Render
        self.stdout.write(f"\n6. Environment Detection:")
        import os
        if os.getenv('RENDER'):
            self.stdout.write("   ✓ Running on Render")
            self.stdout.write("   Note: Render may have network restrictions for SMTP")
        else:
            self.stdout.write("   Running locally")
        
        self.stdout.write(f"\n=== END DEBUG ===")
