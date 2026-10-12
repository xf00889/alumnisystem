"""Copy existing public receipts to private storage before serving donor workflow."""
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from donations.models import Donation
from donations.storage import private_payment_storage


class Command(BaseCommand):
    help = 'Relocate legacy GCash proofs from MEDIA_ROOT to private donation storage.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Perform the copies (default: dry run).')
        parser.add_argument('--remove-public', action='store_true', help='Delete originals after hash verification (requires --apply).')

    def handle(self, *args, **options):
        if options['remove_public'] and not options['apply']:
            raise ValueError('--remove-public requires --apply')
        store = private_payment_storage()
        root = Path(settings.MEDIA_ROOT).resolve()
        moved = 0
        for donation in Donation.objects.exclude(payment_proof='').filter(payment_proof__isnull=False).iterator():
            name = donation.payment_proof.name
            source = (root / name).resolve()
            if root not in source.parents or not source.is_file():
                continue
            destination = Path(store.path(name))
            if options['apply']:
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    destination.write_bytes(source.read_bytes())
                if hashlib.sha256(destination.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
                    raise RuntimeError(f'Receipt verification failed for donation {donation.pk}')
                if options['remove_public']:
                    source.unlink()
            moved += 1
        self.stdout.write(f'{"Copied" if options["apply"] else "Would copy"}: {moved} legacy receipt files')
