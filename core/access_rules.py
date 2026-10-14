"""Role predicates shared by admin-facing alumni and connection workflows."""

def is_administration_account(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and getattr(profile, 'is_alumni_coordinator', False))
