"""Access policy for alumni-only job listings and job-detail endpoints."""
from functools import wraps

from django.shortcuts import redirect


def job_board_login_required(view):
    """Send anonymous requests to the public landing page without a next-URL loop."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:home')
        return view(request, *args, **kwargs)

    return wrapped
