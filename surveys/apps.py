from django.apps import AppConfig


class SurveysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'surveys'
    verbose_name = 'Alumni Surveys and Reports'

    def ready(self):
        import surveys.signals  # noqa
