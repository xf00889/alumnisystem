"""Limited career workspace role. A pure HR account is never general Django staff."""

def is_hr_only(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser or user.is_staff:
        return False
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.is_hr and not profile.is_alumni_coordinator)
