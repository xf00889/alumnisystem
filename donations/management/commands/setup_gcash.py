from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from donations.models import GCashConfig
import base64


class Command(BaseCommand):
    help = 'Create a sample GCash configuration for testing'

    def handle(self, *args, **options):
        # Check if GCash config already exists
        if GCashConfig.objects.exists():
            self.stdout.write(
                self.style.WARNING('GCash configuration already exists. Use Django admin to modify it.')
            )
            return

        # Create a sample GCash configuration
        gcash_config = GCashConfig.objects.create(
            name="NORSU Alumni GCash",
            gcash_number="09123456789",
            account_name="NORSU Alumni Association",
            instructions="""
Important Notes:
• Please include the reference number in your GCash message/notes
• Double-check the amount before sending
• Take a clear screenshot of your payment confirmation
• Donations will be verified within 24 hours during business days
• For urgent concerns, contact us at alumni@norsu.edu.ph
            """.strip(),
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created GCash configuration: {gcash_config.name}\n'
                f'GCash Number: {gcash_config.gcash_number}\n'
                f'Account Name: {gcash_config.account_name}\n\n'
                'IMPORTANT: Please upload a QR code image through the Django admin interface:\n'
                f'Go to: /admin/donations/gcashconfig/{gcash_config.pk}/change/\n'
                'Upload your actual GCash QR code image in the "QR Code Image" field.'
            )
        )
