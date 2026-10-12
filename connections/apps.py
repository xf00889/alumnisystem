from django.apps import AppConfig


class ConnectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'connections'

    def ready(self):
        from . import signals  # noqa: F401 - register message activity receiver
