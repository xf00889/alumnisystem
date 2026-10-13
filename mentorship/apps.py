from django.apps import AppConfig


class MentorshipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mentorship'

    def ready(self):
        from . import circle_signals  # noqa: F401
