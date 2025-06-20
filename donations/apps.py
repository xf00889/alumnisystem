from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DonationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donations'
    verbose_name = _('Donations & Fundraising')

    def ready(self):
        import donations.signals  # noqa
