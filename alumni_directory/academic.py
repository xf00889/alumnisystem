"""Shared academic-code helpers used by registration and profile editing."""


PROFILE_TO_ALUMNI_CAMPUS = {
    "NORSU-MAIN": "MAIN",
    "NORSU-BAIS": "BAIS1",
    "NORSU-GUI": "GUI",
    "NORSU-MAB": "MAB",
    "NORSU-BSC": "BSC",
    "NORSU-SIA": "SIATON",
    "NORSU-PAM": "PAM",
    "OTHER": "MAIN",
    # Historical Education.school codes retained for existing profiles.
    "NORSU-G": "GUI",
    "NORSU-BC": "BAIS1",
    "NORSU-MB": "MAB",
    "NORSU-SC": "SIATON",
    "NORSU-PC": "PAM",
}

ALUMNI_TO_PROFILE_CAMPUS = {
    "MAIN": "NORSU-MAIN",
    "BAIS1": "NORSU-BAIS",
    "BAIS2": "NORSU-BAIS",
    "GUI": "NORSU-GUI",
    "MAB": "NORSU-MAB",
    "BSC": "NORSU-BSC",
    "SIATON": "NORSU-SIA",
    "PAM": "NORSU-PAM",
}


def to_alumni_campus(profile_campus):
    """Translate profile/registration campus codes to ``Alumni.campus`` codes."""
    return PROFILE_TO_ALUMNI_CAMPUS.get(profile_campus, "MAIN")


def to_registration_campus(profile_campus):
    """Normalize historical Education.school codes for the current selector."""
    if profile_campus == "OTHER":
        return "OTHER"
    return ALUMNI_TO_PROFILE_CAMPUS.get(to_alumni_campus(profile_campus), "NORSU-MAIN")
