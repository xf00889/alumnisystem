"""In-app activity notifications for direct and group messages."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from core.models import Notification, NotificationPreference
from .models import DirectMessage


@receiver(post_save, sender=DirectMessage, dispatch_uid="connections.notify_new_direct_message")
def notify_message_recipients(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = instance.conversation
    if conversation.is_group_chat:
        url = reverse("connections:conversations_list") + f"?open_group={conversation.pk}"
        title = f"New message in {conversation.group_name or 'group chat'}"
    else:
        url = reverse("connections:direct_messages", args=[instance.sender_id])
        title = "New message"

    name = instance.sender.get_full_name() or instance.sender.username
    preview = (instance.content or "").strip()[:140] or "Sent an attachment"
    for recipient in conversation.participants.exclude(pk=instance.sender_id):
        if NotificationPreference.objects.filter(user=recipient, app_messages=False).exists():
            continue
        Notification.create_notification(
            recipient=recipient,
            sender=instance.sender,
            notification_type="new_message",
            title=title,
            message=f"{name}: {preview}",
            content_object=instance,
            action_url=url,
        )
