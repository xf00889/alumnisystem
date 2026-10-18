"""Safe full-name and opt-in wildcard matching for the alumni directory.

The wildcard * represents any number of characters in a name.  Wildcards are
never accepted as proof of registrar/graduate eligibility; this module is for
public-directory discovery only.
"""
import re

from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat

MAX_SEARCH_LENGTH = 100
MAX_WILDCARDS = 4


def normalize_directory_search(value):
    """Normalize UI text without altering stored names."""
    return ' '.join((value or '').split())[:MAX_SEARCH_LENGTH].strip()


def alumni_name_condition(search):
    """Return a safe Q condition using full-name aliases supplied below."""
    if '*' in search:
        search = re.sub(r'\*+', '*', search)
        if search.count('*') > MAX_WILDCARDS or not search.replace('*', '').strip():
            return Q(pk__in=[])
        # Literal regex metacharacters are escaped, so only * is a wildcard.
        pattern = '^' + '.*'.join(re.escape(piece) for piece in search.split('*')) + '$'
        return (
            Q(_directory_full_name__iregex=pattern) |
            Q(_directory_reverse_name__iregex=pattern) |
            Q(user__first_name__iregex=pattern) |
            Q(user__last_name__iregex=pattern)
        )

    # A space-separated query matches names held in separate first/last fields,
    # including a middle name, e.g. "Renalyn Andam" -> "Renalyn Mae Andam".
    tokens = search.replace(',', ' ').split()
    if not tokens:
        return Q(pk__in=[])
    parts = Q()
    for token in tokens:
        parts &= Q(_directory_full_name__icontains=token)
    return (
        parts |
        Q(_directory_reverse_name__icontains=search) |
        Q(_directory_full_name__icontains=search)
    )


def with_alumni_name_search(queryset, search):
    """Annotate full names and provide the matching expression for the caller.

    The caller retains existing role-scoped querysets and may OR the name
    condition with other permitted fields for staff-only searches.
    """
    queryset = queryset.annotate(
        _directory_full_name=Concat('user__first_name', Value(' '), 'user__last_name', output_field=CharField()),
        _directory_reverse_name=Concat('user__last_name', Value(' '), 'user__first_name', output_field=CharField()),
    )
    return queryset, alumni_name_condition(search)
