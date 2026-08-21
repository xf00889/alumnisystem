"""Canonical tracer-study labels and report scoping helpers."""

from django.utils import timezone

from .models import Survey


ALUMNI_TITLE = "NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)"
EMPLOYER_TITLE = "NORSU Graduate Tracer Study (EMPLOYER QUESTIONNAIRE)"
TRACER_TITLES = (ALUMNI_TITLE, EMPLOYER_TITLE)


def extract_cycle_label(description):
    """Return the explicit label stored before the tracer description."""
    if description and " — " in description:
        return description.split(" — ", 1)[0].strip()
    return ""


def tracer_audience(survey):
    if survey.title == ALUMNI_TITLE:
        return "alumni"
    if survey.title == EMPLOYER_TITLE:
        return "employer"
    return None


def _date_label(value):
    if value is None:
        return "Not specified"
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%b %d, %Y")


def build_tracer_metadata(survey):
    """Build display-safe metadata for one survey without changing it."""
    audience = tracer_audience(survey)
    is_tracer = audience is not None
    cycle_label = extract_cycle_label(survey.description) if is_tracer else ""

    if audience == "employer":
        target_college = "Not applicable"
        target_program = "Not applicable"
        graduation_year_range = "Not applicable"
    elif audience == "alumni" and survey.display_to_all:
        target_college = "All Colleges"
        target_program = "All Programs"
        graduation_year_range = "All Graduation Years"
    else:
        target_college = (
            survey.get_target_college_display()
            if survey.target_college
            else "All Colleges"
        )
        target_program = survey.target_program or "All Programs"
        year_from = survey.target_graduation_year_from
        year_to = survey.target_graduation_year_to
        if year_from is None and year_to is None:
            graduation_year_range = "All Graduation Years"
        elif year_from is not None and year_to is not None:
            graduation_year_range = f"{year_from}–{year_to}"
        else:
            graduation_year_range = "Not specified"

    return {
        "is_tracer": is_tracer,
        "survey_id": survey.pk,
        "survey_title": survey.title,
        "cycle_label": cycle_label or ("Not specified" if is_tracer else "Not applicable"),
        "audience": audience,
        "audience_label": audience.title() if audience else "Not specified",
        "target_college": target_college if is_tracer else "Not applicable",
        "target_program": target_program if is_tracer else "Not applicable",
        "graduation_year_range": (
            graduation_year_range if is_tracer else "Not applicable"
        ),
        "study_period": f"{_date_label(survey.start_date)} – {_date_label(survey.end_date)}",
        "status": survey.availability_state(),
    }


def resolve_report_survey(report):
    """Return ``(survey, has_reference, missing_reference)`` for a report."""
    parameters = report.parameters if isinstance(report.parameters, dict) else {}
    survey_id = parameters.get("survey_id")
    if survey_id in (None, ""):
        return None, False, False

    try:
        survey_id = int(survey_id)
    except (TypeError, ValueError):
        return None, True, True

    survey = Survey.objects.filter(pk=survey_id).first()
    return survey, True, survey is None
