"""Keep donor payment evidence outside publicly-served MEDIA_ROOT."""
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateDonationStorage(FileSystemStorage):
    def url(self, name):
        raise ValueError('Payment proofs are private; use the staff-only proof view.')


def private_payment_storage():
    location = getattr(settings, 'PRIVATE_DONATION_MEDIA_ROOT', None) or (Path(settings.BASE_DIR) / 'private_donation_media')
    return PrivateDonationStorage(location=str(location), base_url=None)
