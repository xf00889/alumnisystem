"""Recipient-scoped read state for alumni messaging notices.

A notification is emitted for *each message*, but the Messages navigation badge
represents unread conversations.  A DirectMessage.is_read flag is not sufficient
for group chats because it is shared by every recipient.
"""
from urllib.parse import parse_qs, urlsplit

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from core.models import Notification
from .models import DirectConversation, DirectMessage


def _message_content_type():
    return ContentType.objects.get_for_model(DirectMessage)


def clear_conversation_notices(user, conversation):
    """Mark only this user's notices for a conversation read, including old URLs."""
    # Never allow a caller to mark another user's conversation through this helper.
    if not conversation.participants.filter(pk=user.pk).exists():
        return 0

    paths = []
    if conversation.is_group_chat:
        paths.append(reverse('connections:conversations_list') + f'?open_group={conversation.pk}')
    else:
        peer = conversation.participants.exclude(pk=user.pk).first()
        if peer is not None:
            paths.extend([
                reverse('connections:conversations_list') + f'?with={peer.pk}',
                reverse('connections:direct_messages', args=[peer.pk]),
            ])
    messages = DirectMessage.objects.filter(conversation=conversation).values('pk')
    conditions = Q(content_type=_message_content_type(), object_id__in=messages)
    if paths:
        # Older notifications may lack the message GenericForeignKey.
        conditions |= Q(content_type__isnull=True, action_url__in=paths)
    return Notification.objects.filter(
        recipient=user, notification_type='new_message', is_read=False,
    ).filter(conditions).update(is_read=True, read_at=timezone.now())


def unread_conversation_count(user):
    """Count distinct conversations with unread notices, not message events."""
    notices = list(Notification.objects.filter(
        recipient=user, notification_type='new_message', is_read=False,
    ).values_list('content_type_id', 'object_id', 'action_url'))
    if not notices:
        return 0

    message_ct_id = _message_content_type().pk
    message_ids = {
        object_id for content_type_id, object_id, _ in notices
        if content_type_id == message_ct_id and object_id
    }
    messages = {
        row[0]: row[1:]
        for row in DirectMessage.objects.filter(
            pk__in=message_ids, conversation__participants=user,
        ).values_list('pk', 'conversation_id', 'conversation__conversation_type', 'is_read')
    }
    conversation_ids = set()
    fallback_urls = set()
    for ct_id, object_id, action_url in notices:
        if ct_id == message_ct_id and object_id:
            details = messages.get(object_id)
            if details:
                conversation_id, conversation_type, already_read = details
                # Group-chat read state is per recipient, represented by the
                # notification; the message's shared is_read must be ignored.
                if conversation_type == 'group' or not already_read:
                    conversation_ids.add(conversation_id)
        elif ct_id is None and action_url:
            fallback_urls.add(action_url)

    # Support earlier unlinked notices without allowing malformed URLs or
    # notifications for conversations the user cannot access.
    inbox_path = reverse('connections:conversations_list')
    group_ids, peer_ids = set(), set()
    for action_url in fallback_urls:
        url = urlsplit(action_url)
        if url.scheme or url.netloc or url.fragment:
            continue
        if url.path == inbox_path:
            parameters = parse_qs(url.query)
            if len(parameters.get('open_group', [])) == 1:
                value = parameters['open_group'][0]
                if value.isdecimal():
                    group_ids.add(int(value))
            if len(parameters.get('with', [])) == 1:
                value = parameters['with'][0]
                if value.isdecimal():
                    peer_ids.add(int(value))
        elif url.path.startswith(inbox_path) and url.path.endswith('/'):
            value = url.path[len(inbox_path):-1]
            if value.isdecimal():
                peer_ids.add(int(value))
    if group_ids:
        conversation_ids.update(DirectConversation.objects.filter(
            pk__in=group_ids, conversation_type='group', participants=user,
        ).values_list('pk', flat=True))
    if peer_ids:
        conversation_ids.update(DirectConversation.objects.filter(
            conversation_type='direct', participants=user,
        ).filter(participants__pk__in=peer_ids).values_list('pk', flat=True))
    return len(conversation_ids)
