from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = 'Job Board'

    def ready(self):
        try:
            import jobs.signals  # noqa
        except ImportError:
            pass
