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


class CompletedPortalSetupMixin:
    """Run integration tests as though first-run setup has been completed.

    This initializes setup state only inside Django's isolated test database.
    It deliberately does not bypass SetupRequiredMiddleware or change any
    production setup/authentication settings.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from setup.models import SetupState

        SetupState.get_setup_state().mark_complete()
