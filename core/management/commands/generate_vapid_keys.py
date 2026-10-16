"""Generate secure VAPID keys on the VPS once; NEVER commit private key."""
import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create VAPID signing key on the VPS; never overwrite an existing key.'

    def handle(self, *args, **options):
        private_path = Path(settings.BASE_DIR) / '.secrets' / 'web_push_vapid_private.pem'
        private_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if private_path.exists():
            raise CommandError(f'Key already exists at {private_path}. Not overwriting it (existing subscribers depend on the key).')
        private = ec.generate_private_key(ec.SECP256R1())
        encoded = private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(str(private_path), flags, 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(encoded)
        os.chmod(private_path, 0o600)
        public = private.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        public_b64 = base64.urlsafe_b64encode(public).rstrip(b'=').decode('ascii')
        self.stdout.write('Save these variables in the VPS-only .env (NOT in Git):')
        self.stdout.write('WEB_PUSH_VAPID_PRIVATE_KEY=' + str(private_path))
        self.stdout.write('WEB_PUSH_VAPID_PUBLIC_KEY=' + public_b64)
        self.stdout.write('WEB_PUSH_VAPID_SUBJECT=mailto:your-working-alumni-email@example.com')
        self.stdout.write('Replace the example contact email before enabling push.')
