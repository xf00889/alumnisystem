"""Read-only audit for legacy donation records missing payment evidence."""
from django.core.management.base import BaseCommand
from django.db.models import Q
from donations.models import Donation


class Command(BaseCommand):
    help = 'List verification/completed donations missing a stored GCash reference or receipt (read-only).'

    def handle(self, *args, **options):
        missing = (Q(reference_number__isnull=True) | Q(reference_number='') |
                   Q(payment_proof__isnull=True) | Q(payment_proof=''))
        queryset = (Donation.objects.filter(status__in=['pending_verification', 'completed'])
                    .filter(missing).order_by('pk'))
        total = queryset.count()
        self.stdout.write(f'Donations requiring evidence review: {total}')
        for donation in queryset.iterator():
            parts = []
            if not donation.reference_number:
                parts.append('reference')
            if not donation.payment_proof:
                parts.append('proof')
            self.stdout.write(f'  Donation #{donation.pk}: {donation.status}, missing={",".join(parts)}')
        self.stdout.write('No records were modified. Review the evidence with staff before changing any status.')
