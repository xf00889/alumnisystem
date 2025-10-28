"""
Management command to test Brevo API connection
"""
from django.core.management.base import BaseCommand
from core.models.brevo_config import BrevoConfig
import requests
import json

class Command(BaseCommand):
    help = 'Test Brevo API connection and check account status'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, help='Brevo API key to test')
        parser.add_argument('--config-id', type=int, help='Test existing Brevo configuration by ID')

    def handle(self, *args, **options):
        api_key = options.get('api_key')
        config_id = options.get('config_id')
        
        if config_id:
            try:
                config = BrevoConfig.objects.get(id=config_id)
                api_key = config.api_key
                self.stdout.write(f"Testing configuration: {config.name}")
            except BrevoConfig.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Brevo configuration with ID {config_id} not found"))
                return
        
        if not api_key:
            self.stdout.write(self.style.ERROR("Please provide either --api-key or --config-id"))
            return
        
        # Test 1: Check account info
        self.stdout.write("Testing Brevo API connection...")
        headers = {
            'accept': 'application/json',
            'api-key': api_key,
            'content-type': 'application/json'
        }
        
        try:
            # Test account info endpoint
            account_url = "https://api.brevo.com/v3/account"
            response = requests.get(account_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                account_data = response.json()
                self.stdout.write(self.style.SUCCESS("✓ API key is valid"))
                self.stdout.write(f"Account Email: {account_data.get('email', 'N/A')}")
                self.stdout.write(f"Account Status: {account_data.get('plan', 'N/A')}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ API key validation failed: {response.status_code}"))
                self.stdout.write(f"Response: {response.text}")
                return
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"✗ Connection failed: {str(e)}"))
            return
        
        # Test 2: Check SMTP API status
        self.stdout.write("\nTesting SMTP API access...")
        try:
            smtp_url = "https://api.brevo.com/v3/smtp/email"
            test_data = {
                "sender": {
                    "name": "Test Sender",
                    "email": "test@example.com"
                },
                "to": [
                    {
                        "email": "test@example.com",
                        "name": "Test Recipient"
                    }
                ],
                "subject": "Test Email",
                "textContent": "This is a test email to check SMTP API access."
            }
            
            response = requests.post(smtp_url, headers=headers, json=test_data, timeout=10)
            
            if response.status_code == 201:
                self.stdout.write(self.style.SUCCESS("✓ SMTP API is accessible"))
                self.stdout.write("Your Brevo account is ready to send emails!")
            elif response.status_code == 403:
                error_data = response.json()
                self.stdout.write(self.style.WARNING("⚠ SMTP API not activated"))
                self.stdout.write(f"Error: {error_data.get('message', 'Unknown error')}")
                self.stdout.write("\nTo activate SMTP API:")
                self.stdout.write("1. Contact Brevo support at contact@brevo.com")
                self.stdout.write("2. Request SMTP API activation")
                self.stdout.write("3. Provide your account details and use case")
            else:
                self.stdout.write(self.style.ERROR(f"✗ SMTP API test failed: {response.status_code}"))
                self.stdout.write(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"✗ SMTP API test failed: {str(e)}"))
        
        self.stdout.write("\nTest completed!")
