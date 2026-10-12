"""Group community interactions. Always scope reads and mutations to approved members."""
import re
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import GroupEventForm
from .models import (
    AlumniGroup, GroupMembership, Post, PostBookmark, PostReport,
    GroupPoll, GroupPollOption, GroupPollVote, GroupEvent, GroupEventRSVP,
    GroupDiscussion, GroupDiscussionComment, GroupNotification, GroupEventShareRequest,
)


def approved_member(group, user):
    return GroupMembership.objects.filter(group=group, user=user, status='APPROVED', is_active=True).first()


def group_admin(group, user):
    membership = approved_member(group, user)
    return bool(membership and (user.is_staff or membership.role == 'ADMIN'))


def moderator(group, user):
    membership = approved_member(group, user)
    return bool(membership and (user.is_staff or membership.role in ('ADMIN', 'MODERATOR')))


def group_page(group, tab='feed'):
    return f"{reverse('alumni_groups:group_detail', kwargs={'slug': group.slug})}?tab={tab}"


def management_page(group):
    return reverse('alumni_groups:manage_members', kwargs={'slug': group.slug})


def notify_mentions(group, actor, content, post=None):
    """Mentions use exact usernames, limited to approved members in the same group."""
    handles = set(re.findall(r'(?<![\w@])@([A-Za-z0-9_]{1,150})\b', content))
    if not handles:
        return
    members = GroupMembership.objects.filter(
        group=group, status='APPROVED', is_active=True,
        user__username__in=list(handles)[:20]
    ).exclude(user=actor).select_related('user')
    GroupNotification.objects.bulk_create([
        GroupNotification(group=group, recipient=item.user, actor=actor, post=post,
                          message=f'{actor.get_full_name() or actor.username} mentioned you in {group.name[:90]}.')
        for item in members
    ])


@login_required
@require_POST
def toggle_bookmark(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status='APPROVED')
    if not approved_member(post.group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    bookmark, created = PostBookmark.objects.get_or_create(post=post, user=request.user)
    if not created:
        bookmark.delete()
    messages.success(request, 'Post saved.' if created else 'Post removed from saved items.')
    return redirect(group_page(post.group, 'feed'))


@login_required
@require_POST
def report_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status='APPROVED')
    if not approved_member(post.group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    reason = (request.POST.get('reason') or '').strip()
    if not 5 <= len(reason) <= 500:
        return HttpResponseBadRequest('Please provide a reason (5–500 characters).')
    _, created = PostReport.objects.get_or_create(post=post, reporter=request.user, defaults={'reason':reason})
    messages.info(request, 'Report submitted for group review.' if created else 'You already reported this post.')
    return redirect(group_page(post.group, 'feed'))


@login_required
@require_POST
def review_report(request, report_id):
    report = get_object_or_404(PostReport.objects.select_related('post__group'), pk=report_id)
    if not group_admin(report.post.group, request.user):
        return HttpResponseForbidden('Group administrators only.')
    action = request.POST.get('action')
    if action not in ('dismiss', 'resolve', 'remove_post'):
        return HttpResponseBadRequest('Invalid action.')
    report.status = 'DISMISSED' if action == 'dismiss' else 'RESOLVED'
    if action == 'remove_post':
        report.post.status = 'REJECTED'
        report.post.approved_by = request.user
        report.post.approved_at = timezone.now()
        report.post.save(update_fields=['status', 'approved_by', 'approved_at'])
    report.reviewed_by = request.user
    report.save(update_fields=['status', 'reviewed_by'])
    messages.success(request, 'Report reviewed.')
    return redirect(management_page(report.post.group))


@login_required
@require_POST
def pin_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status='APPROVED')
    if not group_admin(post.group, request.user):
        return HttpResponseForbidden('Group administrators only.')
    post.is_pinned = not post.is_pinned
    post.save(update_fields=['is_pinned'])
    messages.success(request, 'Post pinned.' if post.is_pinned else 'Post unpinned.')
    return redirect(group_page(post.group, 'feed'))


@login_required
@require_POST
def create_poll(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug, is_active=True)
    if not approved_member(group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    question = (request.POST.get('question') or '').strip()
    options = [option.strip() for option in request.POST.getlist('options') if option.strip()]
    options = list(dict.fromkeys(options))
    if not 5 <= len(question) <= 250 or not 2 <= len(options) <= 6 or any(len(o)>150 for o in options):
        return HttpResponseBadRequest('Poll needs a question (5–250 characters) and 2–6 distinct options.')
    with transaction.atomic():
        poll = GroupPoll.objects.create(group=group, author=request.user, question=question)
        GroupPollOption.objects.bulk_create([GroupPollOption(poll=poll, label=option) for option in options])
        notify_mentions(group, request.user, question)
    messages.success(request, 'Poll published.')
    return redirect(group_page(group, 'polls'))


@login_required
@require_POST
def vote_poll(request, poll_id):
    poll = get_object_or_404(GroupPoll.objects.select_related('group'), pk=poll_id)
    if not approved_member(poll.group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    if poll.closes_at and poll.closes_at <= timezone.now():
        return HttpResponseBadRequest('Poll has closed.')
    option = get_object_or_404(GroupPollOption, pk=request.POST.get('option'), poll=poll)
    try:
        with transaction.atomic():
            vote, created = GroupPollVote.objects.get_or_create(poll=poll, voter=request.user, defaults={'option':option})
    except IntegrityError:
        created = False
    messages.info(request, 'Vote counted.' if created else 'You already voted in this poll.')
    return redirect(group_page(poll.group, 'polls'))


@login_required
@require_POST
def create_group_event(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug, is_active=True)
    if not group_admin(group, request.user):
        return HttpResponseForbidden('Group administrators only.')
    form = GroupEventForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Could not create the event. Please check dates, venue coordinates and the meeting link.')
        return redirect(group_page(group, 'events'))
    event = form.save(commit=False)
    event.group = group
    event.created_by = request.user
    event.save()
    messages.success(request, 'Group event created. Members may RSVP.')
    return redirect(group_page(group, 'events'))


@login_required
@require_POST
def rsvp_event(request, event_id):
    event = get_object_or_404(GroupEvent.objects.select_related('group'), pk=event_id, is_active=True)
    if not approved_member(event.group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    response = request.POST.get('response')
    if response not in ('GOING', 'MAYBE', 'NOT_GOING'):
        return HttpResponseBadRequest('Invalid response.')
    with transaction.atomic():
        # Lock the event to serialize capacity checks on databases with row-level locking.
        event = GroupEvent.objects.select_for_update().get(pk=event.pk)
        existing = GroupEventRSVP.objects.filter(event=event, user=request.user).first()
        if response == 'GOING' and (not existing or existing.response != 'GOING'):
            if event.max_participants and GroupEventRSVP.objects.filter(event=event, response='GOING').count() >= event.max_participants:
                messages.error(request, 'This event is full.')
                return redirect(group_page(event.group, 'events'))
        GroupEventRSVP.objects.update_or_create(event=event, user=request.user, defaults={'response':response})
    messages.success(request, 'RSVP updated.')
    return redirect(group_page(event.group, 'events'))


@login_required
@require_POST
def create_discussion(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug, is_active=True)
    if not approved_member(group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    title = (request.POST.get('title') or '').strip()
    content = (request.POST.get('content') or '').strip()
    category = request.POST.get('category', 'GENERAL')
    if category not in dict(GroupDiscussion.CATEGORY_CHOICES) or not 5 <= len(title) <= 255 or not 5 <= len(content) <= 5000:
        return HttpResponseBadRequest('Topic needs a title (5–255) and message (5–5000 characters).')
    discussion = GroupDiscussion.objects.create(group=group, created_by=request.user, title=title, content=content, category=category)
    notify_mentions(group, request.user, content)
    messages.success(request, 'Discussion started.')
    return redirect(group_page(group, 'discussions'))


@login_required
@require_POST
def reply_discussion(request, discussion_id):
    discussion = get_object_or_404(GroupDiscussion.objects.select_related('group'), pk=discussion_id)
    if not approved_member(discussion.group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    if discussion.is_locked:
        return HttpResponseForbidden('Discussion is locked.')
    content = (request.POST.get('content') or '').strip()
    if not 1 <= len(content) <= 3000:
        return HttpResponseBadRequest('Reply must contain 1–3000 characters.')
    parent = None
    if request.POST.get('parent_id'):
        parent = get_object_or_404(GroupDiscussionComment, pk=request.POST['parent_id'], discussion=discussion)
        if parent.parent_id:
            parent = parent.parent
    GroupDiscussionComment.objects.create(discussion=discussion, created_by=request.user, content=content, parent=parent)
    notify_mentions(discussion.group, request.user, content)
    messages.success(request, 'Reply added.')
    return redirect(group_page(discussion.group, 'discussions'))


@login_required
@require_POST
def moderate_discussion(request, discussion_id):
    discussion = get_object_or_404(GroupDiscussion.objects.select_related('group'), pk=discussion_id)
    if not moderator(discussion.group, request.user):
        return HttpResponseForbidden('Moderators only.')
    action = request.POST.get('action')
    if action not in ('lock', 'unlock', 'pin', 'unpin'):
        return HttpResponseBadRequest('Invalid action.')
    if action in ('lock', 'unlock'):
        discussion.is_locked = action == 'lock'
        discussion.save(update_fields=['is_locked'])
    else:
        discussion.is_pinned = action == 'pin'
        discussion.save(update_fields=['is_pinned'])
    return redirect(group_page(discussion.group, 'discussions'))


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(GroupNotification, pk=notification_id, recipient=request.user)
    if not approved_member(notification.group, request.user):
        return HttpResponseForbidden('Approved membership required.')
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(group_page(notification.group, 'notifications'))


@login_required
@require_POST
def handle_event_share(request, share_id):
    """Only approved group admins decide whether an announced event appears in their feed."""
    action = request.POST.get('action')
    if action not in ('share', 'pin', 'dismiss'):
        return HttpResponseBadRequest('Invalid sharing action.')
    from .event_sharing import handle_share_request
    with transaction.atomic():
        share = get_object_or_404(
            GroupEventShareRequest.objects.select_for_update().select_related('group', 'event'), pk=share_id
        )
        if not GroupMembership.objects.filter(
            group=share.group, user=request.user, status='APPROVED',
            is_active=True, role='ADMIN'
        ).exists():
            return HttpResponseForbidden('Only an approved group administrator may review this event.')
        if (share.event.status != 'published' or share.event.end_date < timezone.now() or not share.group.is_active or
                not share.event.notified_groups.filter(pk=share.group_id).exists()):
            return HttpResponseBadRequest('This event is no longer available to this group.')
        if not handle_share_request(share, request.user, action):
            messages.info(request, 'This event has already been reviewed.')
            return redirect(group_page(share.group, 'notifications'))
    messages.success(request, {
        'share': 'Event shared as a group post.',
        'pin': 'Event shared and pinned to the group feed.',
        'dismiss': 'Event invitation dismissed.',
    }[action])
    return redirect(group_page(share.group, 'feed' if action in ('share', 'pin') else 'notifications'))
