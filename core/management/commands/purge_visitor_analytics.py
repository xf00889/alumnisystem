"""Delete visitor IP records outside the configured retention window."""
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models.visitor_analytics import DailyVisitor


class Command(BaseCommand):
    help = 'Delete expired visitor IP analytics; schedule daily via cron/systemd.'

    def handle(self, *args, **kwargs):
        retention = max(1, int(settings.VISITOR_ANALYTICS_RETENTION_DAYS))
        before = timezone.localdate() - timedelta(days=retention - 1)
        deleted, _ = DailyVisitor.objects.filter(day__lt=before).delete()
        self.stdout.write(f'Expired visitor analytics rows removed: {deleted}')
