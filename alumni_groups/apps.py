from django.apps import AppConfig


class AlumniGroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alumni_groups'
    verbose_name = 'Alumni Groups'

    def ready(self):
        import alumni_groups.signals  # noqa 