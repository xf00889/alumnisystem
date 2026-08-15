import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from core.models.notifications import Notification
from .models import Survey

logger = logging.getLogger(__name__)


def _tracer_cycle_label(description):
    if description and " — " in description:
        return description.split(" — ", 1)[0]
    return ""


@receiver(post_save, sender=Survey)
def notify_alumni_tracer_survey_active(sender, instance, **kwargs):
    start = instance.start_date
    if start is None or instance.title != "NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)":
        return

    content_type = ContentType.objects.get_for_model(Survey)
    notification_qs = Notification.objects.filter(
        content_type=content_type,
        object_id=instance.pk,
        notification_type="survey",
    )

    from .tracer_study import eligible_alumni_queryset, survey_accepting_responses

    if not survey_accepting_responses(instance):
        # Scheduled, expired, and manually closed cycles should not leave a
        # current call-to-action visible in alumni notifications.
        notification_qs.delete()
        return

    label = _tracer_cycle_label(instance.description)
    title = f"Tracer Study {label} is Now Open" if label else "Tracer Study is Now Open"
    message = (
        "The NORSU Graduate Tracer Study is now accepting responses. "
        "Please take a few minutes to complete the questionnaire."
    )
    action_url = reverse("surveys:tracer_study_alumni")

    alumni_qs = eligible_alumni_queryset(instance)
    eligible_user_ids = alumni_qs.values_list("user_id", flat=True)
    notification_qs.exclude(recipient_id__in=eligible_user_ids).delete()
    existing_recipient_ids = set(
        notification_qs.values_list("recipient_id", flat=True)
    )

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
                if user_id not in existing_recipient_ids
            ]
        )
    except Exception as exc:
        logger.exception(
            f"Failed to create notifications for survey {instance.pk}: {exc}"
        )
