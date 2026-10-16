"""Canonical audience matching for announcement visibility and email recipients."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from accounts.models import Education
from accounts.forms import PostRegistrationForm
from alumni_directory.models import Alumni


# Keep the catalog in sync with the registration model, rather than inventing new
# program/college identifiers. Alumni.course is the canonical program value.
COLLEGE_LABELS = dict(Alumni.COLLEGE_CHOICES)
PROGRAM_LABELS = {}
PROGRAM_ALIASES = {}
for courses in PostRegistrationForm.COURSES_BY_COLLEGE.values():
    for code, label in courses:
        PROGRAM_LABELS[code] = label
        PROGRAM_ALIASES[code.casefold()] = code
        PROGRAM_ALIASES[label.casefold()] = code
for code, label in Education.PROGRAM_CHOICES:
    PROGRAM_LABELS[code] = label
    PROGRAM_ALIASES[code.casefold()] = code
    PROGRAM_ALIASES[label.casefold()] = code


def normalize_target(kind, value):
    """Accept a display name OR a stored code, save a stable code when known."""
    value = ' '.join((value or '').strip().split())
    if kind == 'COLLEGE':
        for code, label in COLLEGE_LABELS.items():
            if value.casefold() in (code.casefold(), label.casefold()):
                return code
        return value
    if kind in ('PROGRAM', 'DEPARTMENT'):
        return PROGRAM_ALIASES.get(value.casefold(), value)
    return value


def audience_label(announcement):
    kind = announcement.target_audience
    value = announcement.target_value
    base = announcement.get_target_audience_display()
    if not value:
        return base
    if kind == 'COLLEGE':
        value = COLLEGE_LABELS.get(value, value)
    elif kind in ('PROGRAM', 'DEPARTMENT'):
        value = PROGRAM_LABELS.get(value, value)
    return f'{base}: {value}'


def manager(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_staff or user.is_superuser:
        return True
    return getattr(getattr(user, 'profile', None), 'is_alumni_coordinator', False)


def audience_q_for_user(user):
    """A Q expression usable BEFORE pagination, so private cards do not leak."""
    public = Q(target_audience='ALL')
    if not getattr(user, 'is_authenticated', False):
        return public
    if manager(user):
        return Q()
    alumnus = getattr(user, 'alumni', None)
    if alumnus is None:
        return public
    year = alumnus.graduation_year
    college = alumnus.college
    course = alumnus.course
    criteria = public
    if isinstance(year, int):
        if 0 <= timezone.now().year - year <= 5:
            criteria |= Q(target_audience='RECENT')
        criteria |= Q(target_audience='BATCH', target_value=str(year))
    if college:
        criteria |= Q(target_audience='COLLEGE', target_value__iexact=college)
    if course:
        # Older department announcements used the category name as a proxy.
        code = normalize_target('PROGRAM', course)
        criteria |= Q(target_audience='DEPARTMENT', target_value__iexact=course)
        criteria |= Q(target_audience='DEPARTMENT', target_value='', category__name__iexact=course)
        criteria |= Q(target_audience='PROGRAM', target_value__iexact=course)
        criteria |= Q(target_audience='PROGRAM', target_value__iexact=code)
        criteria |= Q(target_audience='DEPARTMENT', target_value__iexact=code)
        label = PROGRAM_LABELS.get(code)
        if label:
            criteria |= Q(target_audience='PROGRAM', target_value__iexact=label)
            criteria |= Q(target_audience='DEPARTMENT', target_value__iexact=label)
    return criteria


def visible_announcements_for(user):
    from .models import Announcement
    return Announcement.objects.filter(is_active=True).filter(audience_q_for_user(user))


def announcement_recipients(announcement):
    """Recipient set is restricted on the server, never by frontend selection."""
    User = get_user_model()
    recipients = User.objects.filter(is_active=True)
    kind = announcement.target_audience
    target = (announcement.target_value or '').strip()
    if kind == 'ALL':
        return recipients
    if kind == 'RECENT':
        current = timezone.now().year
        return recipients.filter(alumni__graduation_year__gte=current - 5,
                                 alumni__graduation_year__lte=current).distinct()
    if kind == 'BATCH':
        return recipients.filter(alumni__graduation_year=target).distinct() if target.isdecimal() else recipients.none()
    if kind == 'COLLEGE':
        return recipients.filter(alumni__college__iexact=target).distinct() if target else recipients.none()
    if kind in ('PROGRAM', 'DEPARTMENT'):
        if not target and announcement.category_id and kind == 'DEPARTMENT':
            target = announcement.category.name
        if not target:
            return recipients.none()
        program = normalize_target(kind, target)
        query = Q(alumni__course__iexact=program) | Q(alumni__course__iexact=target)
        label = PROGRAM_LABELS.get(program)
        if label:
            query |= Q(alumni__course__iexact=label)
        return recipients.filter(query).distinct()
    return recipients.none()
