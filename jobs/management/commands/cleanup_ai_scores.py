from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import UserJobAIScore


class Command(BaseCommand):
    help = "Delete stale UserJobAIScore rows older than a retention window."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=getattr(settings, "AI_GLOBAL_SCORE_RETENTION_DAYS", 30),
            help="Retention window in days (default: 30).",
        )

    def handle(self, *args, **options):
        days = max(1, int(options["days"]))
        cutoff = timezone.now() - timedelta(days=days)

        deleted_count, _ = UserJobAIScore.objects.filter(updated_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} AI score rows older than {days} day(s)."
            )
        )
