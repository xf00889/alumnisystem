"""TOTP secret encryption for the built-in django-allauth MFA app.

Keep SECRET_KEY (or MFA_ENCRYPTION_KEY) consistent across Gunicorn workers.
Changing the key without re-encrypting data makes existing TOTP seeds unusable.
"""
import base64
import hashlib
from django.conf import settings
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet, InvalidToken


class NorsuMFAAdapter(DefaultMFAAdapter):
    """Encrypt TOTP secrets at rest, using a purpose-bound key."""

    def _cipher(self):
        source = getattr(settings, 'MFA_ENCRYPTION_KEY', '') or settings.SECRET_KEY
        raw = hashlib.sha256(('norsu-mfa-seed-v1:' + source).encode('utf-8')).digest()
        return Fernet(base64.urlsafe_b64encode(raw))

    def encrypt(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError('TOTP secret must be a string')
        return 'v1:' + self._cipher().encrypt(text.encode('utf-8')).decode('ascii')

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text.startswith('v1:'):
            # All secrets managed by this integration MUST have an encrypted prefix.
            # Fail closed rather than accepting unencrypted legacy secrets.
            raise ValueError('Unsupported encrypted TOTP secret format')
        try:
            return self._cipher().decrypt(encrypted_text[3:].encode('ascii')).decode('utf-8')
        except InvalidToken as exc:
            raise ValueError('Unable to decrypt TOTP secret: check MFA encryption key') from exc
