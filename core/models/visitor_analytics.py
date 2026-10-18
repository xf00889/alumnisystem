"""Daily aggregated visitor IPs. Personal data: superuser access, short retention."""
from django.db import models


class DailyVisitor(models.Model):
    day = models.DateField(db_index=True)
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField(db_index=True)
    sampled_page_loads = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('day', 'ip_address'), name='unique_site_visitor_per_day'),
        ]
        indexes = [models.Index(fields=('day', 'last_seen'), name='site_visitor_day_seen_idx')]
        ordering = ('-last_seen',)

    def __str__(self):
        return f'{self.ip_address} on {self.day}'
