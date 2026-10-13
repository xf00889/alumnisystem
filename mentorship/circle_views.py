"""A private mentor-wide workspace; no access is granted via a client-supplied mentor ID."""
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from accounts.models import Mentor, MentorshipRequest
from .circle_forms import MentorCircleMeetingForm
from core.rate_limiters import rate_limit_messages
from .models import MentorCircleEntry, MentorCircleMeeting, MentorshipProgress


def _circle_access(request, mentor_id):
    mentor = get_object_or_404(Mentor.objects.select_related('user'), pk=mentor_id)
    is_mentor = request.user.pk == mentor.user_id
    is_mentee = MentorshipRequest.objects.filter(
        mentor=mentor, mentee=request.user, status='APPROVED'
    ).exists()
    if not (is_mentor or is_mentee):
        raise Http404('Group not found')
    return mentor, is_mentor


def _visible_entries(mentor, user, is_mentor):
    queryset = MentorCircleEntry.objects.filter(mentor=mentor).select_related(
        'author', 'mentorship__mentee', 'meeting'
    )
    if is_mentor:
        return queryset
    # Group announcements are visible only if they have no targeted mentorship and
    # no restricted meeting, or if the user was included in the meeting when created.
    return queryset.filter(
        Q(mentorship__mentee=user, mentorship__status='APPROVED') |
        Q(mentorship__isnull=True, meeting__isnull=True) |
        Q(meeting__participants__mentee=user, meeting__participants__status='APPROVED')
    ).distinct()


def _entries_context(mentor, user, is_mentor):
    entries = list(_visible_entries(mentor, user, is_mentor).order_by('-created_at', '-pk')[:80])
    entries.reverse()
    return {
        'entries': entries,
        'current_user': user,
        'mentor': mentor,
        'is_circle_mentor': is_mentor,
    }


@login_required
@require_GET
def mentor_circle(request, mentor_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    active = list(MentorshipRequest.objects.filter(
        mentor=mentor, status='APPROVED'
    ).select_related('mentee').order_by('mentee__first_name', 'mentee__last_name'))
    meetings = MentorCircleMeeting.objects.filter(
        mentor=mentor, is_cancelled=False, meeting_date__gte=timezone.now()
    ).prefetch_related('participants')
    if not is_mentor:
        meetings = meetings.filter(participants__mentee=request.user).distinct()
    context = {
        'mentor': mentor, 'is_circle_mentor': is_mentor,
        'circle_members': active, 'circle_meetings': meetings[:20],
        **_entries_context(mentor, request.user, is_mentor),
    }
    return render(request, 'mentorship/mentor_circle.html', context)


@login_required
@require_GET
def circle_activity(request, mentor_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    return render(request, 'mentorship/partials/circle_activity.html', _entries_context(mentor, request.user, is_mentor))


@login_required
@require_POST
@rate_limit_messages(max_messages=20, time_window=60)
def circle_send(request, mentor_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not mentor.is_active:
        return JsonResponse({'error': 'Mentor account is inactive.'}, status=403)
    content = request.POST.get('content', '').strip()
    if not content or len(content) > 2000:
        return JsonResponse({'error': 'Enter a message between 1 and 2,000 characters.'}, status=400)
    MentorCircleEntry.objects.create(mentor=mentor, author=request.user, kind='MESSAGE', body=content)
    return JsonResponse({'success': True})


@login_required
@require_POST
def circle_schedule(request, mentor_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not is_mentor or not mentor.is_active:
        return JsonResponse({'error': 'Only the active group mentor may schedule meetings.'}, status=403)
    form = MentorCircleMeetingForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Please check the meeting details.', 'fields': form.errors.get_json_data()}, status=400)
    with transaction.atomic():
        participants = list(MentorshipRequest.objects.select_for_update().filter(
            mentor=mentor, status='APPROVED'
        ))
        if not participants:
            return JsonResponse({'error': 'Accept a mentee before scheduling a group meeting.'}, status=400)
        meeting = form.save(commit=False)
        meeting.mentor = mentor
        meeting.save()
        meeting.participants.set(participants)
        MentorCircleEntry.objects.create(
            mentor=mentor, author=request.user, kind='MEETING', meeting=meeting,
            title=f'Group meeting: {meeting.title}',
            body=f'{meeting.meeting_date:%b %d, %Y at %I:%M %p} · {meeting.duration} minutes',
        )
    return JsonResponse({'success': True, 'meeting_id': meeting.pk, 'participants': len(participants)})


@login_required
@require_POST
def circle_cancel_meeting(request, mentor_id, meeting_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not is_mentor or not mentor.is_active:
        return JsonResponse({'error': 'Only the active group mentor may cancel meetings.'}, status=403)
    with transaction.atomic():
        meeting = get_object_or_404(
            MentorCircleMeeting.objects.select_for_update(), pk=meeting_id, mentor=mentor
        )
        if meeting.is_cancelled:
            return JsonResponse({'error': 'Meeting was already cancelled.'}, status=409)
        meeting.is_cancelled = True
        meeting.save(update_fields=['is_cancelled'])
        MentorCircleEntry.objects.create(
            mentor=mentor, author=request.user, kind='MEETING', meeting=meeting,
            title=f'Meeting cancelled: {meeting.title}', body='The mentor has cancelled this group meeting.',
        )
    return JsonResponse({'success': True})


@login_required
@require_POST
def circle_update_progress(request, mentor_id, mentorship_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not is_mentor or not mentor.is_active:
        return JsonResponse({'error': 'Only the active mentor can update mentee progress.'}, status=403)
    try:
        percentage = int(request.POST.get('percentage', ''))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Enter a progress value from 0 to 100.'}, status=400)
    note = request.POST.get('note', '').strip()
    if not 0 <= percentage <= 100 or not note or len(note) > 2000:
        return JsonResponse({'error': 'Provide a progress value and a note (max 2,000 characters).'}, status=400)
    with transaction.atomic():
        mentorship = get_object_or_404(
            MentorshipRequest.objects.select_for_update(), pk=mentorship_id,
            mentor=mentor, status='APPROVED'
        )
        MentorshipProgress.objects.create(
            mentorship=mentorship, title='Mentorship progress', description=note, created_by=request.user
        )
        mentorship.progress_percentage = percentage
        mentorship.save(update_fields=['progress_percentage', 'updated_at'])
    return JsonResponse({'success': True})



def _parse_timeline_submission(request):
    end_date = request.POST.get('expected_end_date', '').strip()
    try:
        parsed_date = date.fromisoformat(end_date) if end_date else None
    except ValueError:
        raise ValueError('Enter a valid expected end date.')
    if parsed_date and parsed_date < timezone.now().date():
        raise ValueError('Expected end date cannot be in the past.')

    periods = request.POST.getlist('period[]')
    descriptions = request.POST.getlist('description[]')
    statuses = request.POST.getlist('status[]')
    if not periods or len(periods) != len(descriptions) or len(periods) != len(statuses) or len(periods) > 25:
        raise ValueError('Add between 1 and 25 complete milestones.')

    notes = request.POST.get('notes', '').strip()
    if len(notes) > 2000:
        raise ValueError('Notes must be 2,000 characters or fewer.')

    lines = []
    for period, description, milestone_status in zip(periods, descriptions, statuses):
        period, description = period.strip(), description.strip()
        if (
            not period or not description or len(period) > 40 or len(description) > 300
            or any(c in period + description for c in '\r\n[]')
            or milestone_status not in ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED')
        ):
            raise ValueError('Each milestone needs a period, description, and valid status.')
        lines.append(f'Week/Day {period}: {description} [{milestone_status}]')

    timeline_text = '\n'.join(lines) + ('\n\nNotes:\n' + notes if notes else '')
    return parsed_date, timeline_text


@login_required
@require_POST
def circle_update_group_progress(request, mentor_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not is_mentor or not mentor.is_active:
        return JsonResponse({'error': 'Only the active mentor can update group progress.'}, status=403)
    try:
        percentage = int(request.POST.get('percentage', ''))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Enter a progress value from 0 to 100.'}, status=400)
    note = request.POST.get('note', '').strip()
    if not 0 <= percentage <= 100 or not note or len(note) > 2000:
        return JsonResponse({'error': 'Provide a progress value and a note (max 2,000 characters).'}, status=400)

    with transaction.atomic():
        mentees = list(MentorshipRequest.objects.select_for_update().filter(
            mentor=mentor, status='APPROVED'
        ))
        if not mentees:
            return JsonResponse({'error': 'Accept a mentee before posting a group progress update.'}, status=400)
        for mentorship in mentees:
            MentorshipProgress.objects.create(
                mentorship=mentorship,
                title='Group progress update',
                description=note,
                created_by=request.user,
            )
            mentorship.progress_percentage = percentage
            mentorship.save(update_fields=['progress_percentage', 'updated_at'])
    return JsonResponse({'success': True, 'participants': len(mentees)})


@login_required
@require_POST
def circle_update_group_timeline(request, mentor_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not is_mentor or not mentor.is_active:
        return JsonResponse({'error': 'Only the active mentor can manage the group timeline.'}, status=403)
    try:
        parsed_date, timeline_text = _parse_timeline_submission(request)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    with transaction.atomic():
        mentees = list(MentorshipRequest.objects.select_for_update().filter(
            mentor=mentor, status='APPROVED'
        ))
        if not mentees:
            return JsonResponse({'error': 'Accept a mentee before setting a shared timeline.'}, status=400)
        for mentorship in mentees:
            mentorship.timeline_milestones = timeline_text
            mentorship.expected_end_date = parsed_date
            mentorship.save(update_fields=['timeline_milestones', 'expected_end_date', 'updated_at'])
    return JsonResponse({'success': True, 'participants': len(mentees)})


@login_required
@require_POST
def circle_update_timeline(request, mentor_id, mentorship_id):
    mentor, is_mentor = _circle_access(request, mentor_id)
    if not is_mentor or not mentor.is_active:
        return JsonResponse({'error': 'Only the active mentor can manage mentee timelines.'}, status=403)
    try:
        parsed_date, timeline_text = _parse_timeline_submission(request)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    with transaction.atomic():
        mentorship = get_object_or_404(
            MentorshipRequest.objects.select_for_update(), pk=mentorship_id,
            mentor=mentor, status='APPROVED'
        )
        mentorship.timeline_milestones = timeline_text
        mentorship.expected_end_date = parsed_date
        mentorship.save(update_fields=['timeline_milestones', 'expected_end_date', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def cancel_personal_meeting(request, meeting_id):
    """Retain legacy individual meeting history rather than deleting the row."""
    from .models import MentorshipMeeting
    with transaction.atomic():
        meeting = get_object_or_404(
            MentorshipMeeting.objects.select_for_update().select_related('mentorship__mentor'),
            pk=meeting_id, mentorship__mentor__user=request.user,
            mentorship__status='APPROVED', status='SCHEDULED',
        )
        meeting.status = 'CANCELLED'
        meeting.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'success': True})
