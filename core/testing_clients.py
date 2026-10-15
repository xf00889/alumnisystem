"""Django test clients that exercise HTTPS routes without weakening production settings."""

from django.test import Client


class HTTPSClient(Client):
    """Send requests over HTTPS by default; allow explicit overrides in tests."""

    def get(self, path, *args, **kwargs):
        kwargs.setdefault('secure', True)
        return super().get(path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        kwargs.setdefault('secure', True)
        return super().post(path, *args, **kwargs)
