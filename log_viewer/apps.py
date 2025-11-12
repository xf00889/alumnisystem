from django.apps import AppConfig


class LogViewerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'log_viewer'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import log_viewer.signals  # noqa