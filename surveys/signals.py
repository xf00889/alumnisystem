import logging
from datetime import date as date_class
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from alumni_directory.models import Alumni
from core.models.notifications import Notification
from .models import Survey

logger = logging.getLogger(__name__)


def _tracer_cycle_label(description):
    if description and " — " in description:
        return description.split(" — ", 1)[0]
    return ""


@receiver(post_save, sender=Survey)
def notify_alumni_tracer_survey_active(sender, instance, **kwargs):
    # Type-safe date comparison: normalize both sides to compare dates
    start = instance.start_date
    if start is None:
        return
    
    # Check if start date is in the future (whether date or datetime)
    # Normalize to naive datetime for safe comparison
    if isinstance(start, date_class) and not isinstance(start, datetime):
        # Plain date object: convert to naive datetime at midnight
        start_cmp = datetime.combine(start, datetime.min.time())
    else:
        # Datetime object: strip timezone if present for naive comparison
        start_cmp = start.replace(tzinfo=None) if start.tzinfo else start
    
    # Compare with naive now
    now_cmp = timezone.now().replace(tzinfo=None)
    
    if start_cmp > now_cmp:
        return
    
    if (
        instance.title != "NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)"
        or instance.status != "active"
    ):
        return

    content_type = ContentType.objects.get_for_model(Survey)
    if Notification.objects.filter(
        content_type=content_type,
        object_id=instance.pk,
        notification_type="survey",
    ).exists():
        return

    label = _tracer_cycle_label(instance.description)
    title = f"Tracer Study {label} is Now Open" if label else "Tracer Study is Now Open"
    message = (
        "The NORSU Graduate Tracer Study is now accepting responses. "
        "Please take a few minutes to complete the questionnaire."
    )
    action_url = reverse("surveys:tracer_study_alumni")

    alumni_qs = Alumni.objects.all()
    if not instance.display_to_all:
        alumni_qs = alumni_qs.filter(college=instance.target_college)

    try:
        Notification.objects.bulk_create(
            [
                Notification(
                    recipient_id=user_id,
                    notification_type="survey",
                    title=title,
                    message=message,
                    content_type=content_type,
                    object_id=instance.pk,
                    action_url=action_url,
                )
                for user_id in alumni_qs.values_list("user_id", flat=True)
            ]
        )
    except Exception as exc:
        logger.exception(
            f"Failed to create notifications for survey {instance.pk}: {exc}"
        )
