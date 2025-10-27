"""
Test the exact web form submission process for unauthenticated users
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from donations.models import Campaign
from django.contrib.auth.models import AnonymousUser
import json

class Command(BaseCommand):
    help = 'Test web form submission for unauthenticated users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        # Create a test client
        client = Client()
        
        # Get a campaign
        campaign = Campaign.objects.first()
        if not campaign:
            self.stdout.write(self.style.ERROR('No campaigns found. Please create a campaign first.'))
            return
        
        self.stdout.write(f'Testing with campaign: {campaign.name}')
        
        # Simulate the exact POST request that would be sent from the web form
        form_data = {
            'amount': '200.00',
            'donor_name': 'Web Form Test Donor',
            'donor_email': email,
            'message': 'Testing web form submission for unauthenticated users',
            'is_anonymous': False,
            'csrfmiddlewaretoken': 'test-token'  # This would be handled by the form
        }
        
        # Get the campaign detail URL
        url = reverse('donations:campaign_detail', kwargs={'slug': campaign.slug})
        
        self.stdout.write(f'Submitting POST request to: {url}')
        
        try:
            # First, get the page to get the CSRF token
            response = client.get(url)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Failed to get campaign page: {response.status_code}'))
                return
            
            # Extract CSRF token from the response
            csrf_token = None
            if 'csrfmiddlewaretoken' in response.content.decode():
                # This is a simplified way to get the token
                csrf_token = 'test-csrf-token'
            
            # Update form data with CSRF token
            form_data['csrfmiddlewaretoken'] = csrf_token
            
            # Submit the form
            response = client.post(url, data=form_data, follow=True)
            
            self.stdout.write(f'Response status: {response.status_code}')
            self.stdout.write(f'Response URL: {response.request["PATH_INFO"]}')
            
            if response.status_code == 200:
                # Check if we were redirected to payment instructions
                if 'payment' in response.request['PATH_INFO']:
                    self.stdout.write(self.style.SUCCESS('✅ Form submission successful!'))
                    self.stdout.write(self.style.SUCCESS('✅ Redirected to payment instructions'))
                    self.stdout.write(self.style.SUCCESS('✅ Check your email for the confirmation!'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️ Form submitted but not redirected to payment instructions'))
                    self.stdout.write(f'Final URL: {response.request["PATH_INFO"]}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Form submission failed with status: {response.status_code}'))
                
                # Check for form errors
                if hasattr(response, 'context') and 'form' in response.context:
                    form = response.context['form']
                    if form.errors:
                        self.stdout.write(self.style.ERROR(f'Form errors: {form.errors}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during test: {str(e)}'))
        
        # Check if a donation was created
        from donations.models import Donation
        latest_donation = Donation.objects.filter(donor_email=email).order_by('-created_at').first()
        if latest_donation:
            self.stdout.write(f'Latest donation found: ID {latest_donation.pk}, Status: {latest_donation.status}')
        else:
            self.stdout.write(self.style.WARNING('No donation found with the test email'))
