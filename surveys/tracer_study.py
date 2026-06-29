"""
Dedicated views for the NORSU Graduate Tracer Study.

The questionnaire data is still stored in the generic ``Survey`` model (so it
can be reported on like any other survey), but the user-facing form lives at
its own URL with its own template, so it doesn't feel like a generic survey.

URLs:
* ``/tracer-study/``         - Alumni (login required, one response per alumni)
* ``/tracer-study/employer/`` - Employers (public; auto-creates an Employer
                                record on first submission and reuses it
                                thereafter)
"""
from datetime import date
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import View

from alumni_directory.models import Alumni
from .models import (
    Employer,
    EmployerResponse,
    EmployerResponseAnswer,
    QuestionOption,
    Report,
    ResponseAnswer,
    Survey,
    SurveyQuestion,
    SurveyResponse,
)


ALUMNI_TITLE = "NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)"
EMPLOYER_TITLE = "NORSU Graduate Tracer Study (EMPLOYER QUESTIONNAIRE)"


def _can_view_tracer_reports(user):
    return (
        user.is_staff
        or user.is_superuser
        or (hasattr(user, "profile") and user.profile.is_alumni_coordinator)
    )


def _alumni_response_rows(survey):
    responses = {
        response.alumni_id: response
        for response in SurveyResponse.objects.filter(survey=survey).select_related("alumni__user")
    }
    rows = []
    for alumni in Alumni.objects.select_related("user").order_by("user__last_name", "user__first_name"):
        response = responses.get(alumni.id)
        rows.append({
            "id": alumni.id,
            "name": alumni.full_name or alumni.user.username,
            "email": alumni.user.email,
            "course": alumni.course,
            "graduation_year": alumni.graduation_year,
            "status": "Responded" if response else "Not Responded",
            "submitted_at": response.submitted_at if response else None,
        })
    return rows


def _get_active_survey(title):
    return get_object_or_404(Survey, title=title, status="active")


# ---------------------------------------------------------------------------
# Alumni profile -> question prefill
# ---------------------------------------------------------------------------
#
# Map ``Alumni`` (and its user/profile) fields to the tracer-study question
# ``key``s defined in ``seed_tracer_study.ALUMNI_QUESTIONS``. The prefill is
# only used when the field has a value in the system; missing/blank values
# leave the form field empty so the alumni can fill it in themselves.
#
# Returned dict format: ``{question_id: prefill_value}`` where prefill_value
# is a string for text-like types and an ``option.id`` (int) for
# ``multiple_choice``.

# Alumni.gender choices -> questionnaire value_keys for p1_gender
_GENDER_VALUE_KEY = {"M": "male", "F": "female", "O": "other"}

# Alumni.campus choices -> questionnaire value_keys for p2_campus.
# Alumni combines Main I + II into a single MAIN choice; default to Main I.
_CAMPUS_VALUE_KEY = {
    "MAIN": "main1",
    "BAIS1": "bais", "BAIS2": "bais",
    "BSC": "bayawan", "SIATON": "siaton", "GUI": "guihulngan",
    "PAM": "pamplona", "MAB": "mabinay",
}

# Profile.education.school choices -> questionnaire value_keys for p2_campus.
# Used as a secondary source when Alumni.campus is blank.
_EDUCATION_CAMPUS_VALUE_KEY = {
    "NORSU-MAIN": "main1",
    "NORSU-G": "guihulngan",
    "NORSU-BC": "bais",     # Bais City — Bais Campuses
    "NORSU-BSC": "bayawan",
    "NORSU-MB": "mabinay",
    "NORSU-SC": "siaton",
    "NORSU-PC": "pamplona",
    # "OTHER" / blank / null: no match
}

# Alumni.employment_status -> p3_employed value_key
_EMPLOYED_VALUE_KEY = {
    "EMPLOYED_FULL": "yes", "EMPLOYED_PART": "yes",
    "SELF_EMPLOYED": "yes", "INTERN": "yes",
    "UNEMPLOYED": "no", "STUDENT": "no", "RETIRED": "no",
}


def _compute_age(birth_date):
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _campus_from_education(profile):
    """Pick a campus value_key from the most recent / primary Education row.

    Returns None if profile is missing or has no education rows with a
    mappable school code.
    """
    if profile is None:
        return None
    edu_qs = profile.education.exclude(school__isnull=True).exclude(school="")
    # Prefer the primary record; otherwise the most recent graduation year.
    primary = edu_qs.filter(is_primary=True).first()
    if primary is None:
        primary = edu_qs.order_by("-graduation_year", "-id").first()
    if primary is None:
        return None
    return _EDUCATION_CAMPUS_VALUE_KEY.get(primary.school)


def _alumni_prefill_source(alumni):
    """Return {question_key: source_value} for any prefillable field.

    The source value is the raw Alumni/Profile data; the view layer is
    responsible for turning it into a concrete question value (option id
    vs text) when it builds the per-question prefill dict.
    """
    user = alumni.user
    profile = getattr(user, "profile", None)

    dob = alumni.date_of_birth
    if not dob and profile is not None:
        dob = getattr(profile, "birth_date", None)

    address_parts = filter(None, [
        alumni.address, alumni.city, alumni.province,
        str(alumni.country.name) if alumni.country else None,
    ])
    address = ", ".join(address_parts) if address_parts else None

    course = alumni.course or None
    if course and alumni.major:
        course = f"{course} - {alumni.major}"

    # Campus: prefer Alumni.campus, fall back to Profile.education.school.
    campus = _CAMPUS_VALUE_KEY.get(alumni.campus) or _campus_from_education(profile)

    return {
        "p1_name": (user.get_full_name() or user.username) or None,
        "p1_address": address,
        "p1_email": user.email or None,
        "p1_contact": str(alumni.phone_number) if alumni.phone_number else None,
        "p1_dob": dob.isoformat() if dob else None,
        "p1_gender": _GENDER_VALUE_KEY.get(alumni.gender),
        "p1_fb": (getattr(profile, "facebook_profile", "") or "") or None,
        "p1_twitter": (getattr(profile, "twitter_profile", "") or "") or None,
        "p2_course": course,
        "p2_year": str(alumni.graduation_year) if alumni.graduation_year else None,
        "p2_campus": campus,
        "p3_employed": _EMPLOYED_VALUE_KEY.get(alumni.employment_status),
        "p3_position": alumni.job_title or None,
        "p3_company": alumni.current_company or None,
    }


def _build_prefill_for_alumni(alumni, survey):
    """Resolve the prefill source into {question_id: prefill_value}.

    The same Alumni record can power many question types; this function
    walks the survey's questions, looks up the source value by ``key``,
    and resolves multiple-choice value_keys to option ids.
    """
    source = _alumni_prefill_source(alumni)
    if not source:
        return {}

    result = {}
    for question in survey.questions.all().prefetch_related("options"):
        try:
            meta = json.loads(question.help_text) if question.help_text else {}
        except (ValueError, TypeError):
            meta = {}
        key = meta.get("key")
        if not key or key not in source:
            continue
        value = source[key]
        if value is None or value == "":
            continue

        if question.question_type in ("text", "email", "phone", "number", "date", "url"):
            result[question.id] = str(value)
        elif question.question_type == "multiple_choice":
            opt = _resolve_option_id(question, key, str(value))
            if opt is not None:
                result[question.id] = opt.id
        # checkbox and rating/likert are intentionally not prefilled: the
        # source data doesn't carry structured multi-select or subjective
        # answers, and we'd rather not seed a partial selection.
    return result


# Per-question matchers for multiple-choice prefill. ``QuestionOption`` has
# no ``value_key`` column (the seeder dropped it silently), so we look up
# options by lowercased option_text for some questions and by a keyword
# mapping for others. The mapping is keyed by the question's prefill key
# (the same key used in ``ALUMNI_QUESTIONS`` in ``seed_tracer_study``).

_CAMPUS_KEYWORDS = {
    "main1": ["main campus i"],
    "main2": ["main campus ii"],
    "bayawan": ["bayawan"],
    "siaton": ["siaton"],
    "guihulngan": ["guihulngan"],
    "bais": ["bais"],
    "mabinay": ["mabinay"],
    "pamplona": ["pamplona"],
}


def _resolve_option_id(question, question_key, value_key):
    """Find the option in ``question`` that matches ``value_key``.

    Returns the QuestionOption or None. Uses a per-question strategy:
    exact case-insensitive option_text match, with a fallback to substring
    matching for known variants (e.g. "other (please specify)" -> "other").
    """
    options = list(question.options.all())
    if not options:
        return None

    if question_key == "p2_campus":
        for kw in _CAMPUS_KEYWORDS.get(value_key, []):
            for opt in options:
                if kw in opt.option_text.lower():
                    return opt
        return None

    # Default: case-insensitive match against option_text. "yes" / "no" /
    # "never" map cleanly; "other" matches "Other (please specify)" via
    # substring fallback.
    for opt in options:
        if opt.option_text.strip().lower() == value_key.lower():
            return opt
    for opt in options:
        if value_key.lower() in opt.option_text.lower():
            return opt
    return None


def _already_submitted_alumni(survey, alumni):
    return SurveyResponse.objects.filter(survey=survey, alumni=alumni).exists()


def _save_alumni_response(request, survey, alumni):
    """Create a SurveyResponse + ResponseAnswer rows for the alumni tracer study.

    Returns the new ``SurveyResponse`` instance. Mirrors the post logic in
    ``SurveyTakeView.post`` but writes to the dedicated tracer-study URL on
    success instead of the generic survey list.
    """
    response = SurveyResponse.objects.create(
        survey=survey,
        alumni=alumni,
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    answer_count = 0
    for question in survey.questions.all().prefetch_related("options"):
        field_name = f"question_{question.id}"
        answer_data = {}

        if question.question_type in (
            "text", "email", "number", "phone", "url", "date", "time",
        ):
            value = request.POST.get(field_name, "").strip()
            if value:
                answer_data["text_answer"] = value

        elif question.question_type == "multiple_choice":
            option_id = request.POST.get(field_name)
            if option_id:
                try:
                    option = QuestionOption.objects.get(id=option_id)
                    answer_data["selected_option"] = option
                    if option.allow_custom:
                        custom = request.POST.get(
                            f"{field_name}_other", ""
                        ).strip()
                        if custom:
                            answer_data["custom_text"] = custom
                except QuestionOption.DoesNotExist:
                    pass

        elif question.question_type == "checkbox":
            for option in question.options.all():
                if request.POST.get(f"{field_name}_{option.id}"):
                    custom = ""
                    if option.allow_custom:
                        custom = request.POST.get(
                            f"{field_name}_other_{option.id}", ""
                        ).strip()
                    ResponseAnswer.objects.create(
                        response=response,
                        question=question,
                        selected_option=option,
                        custom_text=custom,
                    )
                    answer_count += 1
            continue

        elif question.question_type in ("rating", "likert"):
            rating = request.POST.get(field_name)
            if rating:
                try:
                    answer_data["rating_value"] = int(rating)
                except (TypeError, ValueError):
                    pass

        if answer_data:
            ResponseAnswer.objects.create(
                response=response, question=question, **answer_data
            )
            answer_count += 1

    return response, answer_count


def _find_or_create_employer(company_name, position):
    employer, _ = Employer.objects.get_or_create(
        company_name=company_name.strip(),
        position=position.strip(),
    )
    return employer


def _save_employer_response(request, survey, employer):
    response = EmployerResponse.objects.create(
        survey=survey,
        employer=employer,
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    answer_count = 0
    for question in survey.questions.all().prefetch_related("options"):
        field_name = f"question_{question.id}"
        answer_data = {}

        if question.question_type in (
            "text", "email", "number", "phone", "url", "date", "time",
        ):
            value = request.POST.get(field_name, "").strip()
            if value:
                answer_data["text_answer"] = value

        elif question.question_type in ("rating", "likert"):
            rating = request.POST.get(field_name)
            if rating:
                try:
                    answer_data["rating_value"] = int(rating)
                except (TypeError, ValueError):
                    pass

        elif question.question_type in ("multiple_choice", "checkbox"):
            # Employer questionnaire currently has no MC/checkbox questions,
            # but support them defensively.
            option_id = request.POST.get(field_name)
            if option_id:
                try:
                    answer_data["selected_option"] = QuestionOption.objects.get(
                        id=option_id
                    )
                except QuestionOption.DoesNotExist:
                    pass

        if answer_data:
            EmployerResponseAnswer.objects.create(
                response=response, question=question, **answer_data
            )
            answer_count += 1

    return response, answer_count


@require_http_methods(["GET", "POST"])
@login_required
def tracer_study_alumni(request):
    survey = _get_active_survey(ALUMNI_TITLE)
    # Authed users without an alumni profile fall into one of two cases:
    #   * Staff / superuser / alumni coordinator without an Alumni row —
    #     they have no business taking the survey themselves; send them
    #     to the reports dashboard where the data lives.
    #   * Regular authed user who hasn't completed alumni registration —
    #     send them to the post-registration page so they can finish
    #     creating their Alumni profile.
    if not Alumni.objects.filter(user=request.user).exists():
        is_staff_like = (
            request.user.is_staff
            or request.user.is_superuser
            or (hasattr(request.user, "profile")
                and request.user.profile.is_alumni_coordinator)
        )
        if is_staff_like:
            return redirect("surveys:tracer_study_reports")
        messages.info(
            request,
            "Please complete your alumni registration before taking the Tracer Study.",
        )
        return redirect("accounts:post_registration")
    alumni = Alumni.objects.get(user=request.user)

    if _already_submitted_alumni(survey, alumni):
        return render(
            request,
            "tracer_study/already_submitted.html",
            {"survey": survey, "audience": "alumni"},
        )

    if request.method == "POST":
        try:
            with transaction.atomic():
                _save_alumni_response(request, survey, alumni)
        except Exception as exc:  # pragma: no cover - defensive
            messages.error(
                request,
                "An error occurred while submitting your response. Please try again.",
            )
            return redirect("surveys:tracer_study_alumni")

        return render(
            request,
            "tracer_study/thank_you.html",
            {"survey": survey, "audience": "alumni"},
        )

    questions = survey.questions.all().prefetch_related("options")
    prefill_answers = _build_prefill_for_alumni(alumni, survey)
    return render(
        request,
        "tracer_study/alumni_form.html",
        {
            "survey": survey,
            "questions": questions,
            "alumni": alumni,
            "prefill_answers": prefill_answers,
        },
    )


@require_http_methods(["GET", "POST"])
def tracer_study_employer(request):
    survey = _get_active_survey(EMPLOYER_TITLE)

    if request.method == "POST":
        company = request.POST.get("company_name", "").strip()
        position = request.POST.get("position", "").strip()
        if not company or not position:
            messages.error(
                request,
                "Company Name and Position are required before submitting.",
            )
            return redirect("surveys:tracer_study_employer")

        if EmployerResponse.objects.filter(survey=survey, employer__company_name=company).exists():
            return render(
                request,
                "tracer_study/already_submitted.html",
                {"survey": survey, "audience": "employer"},
            )

        try:
            with transaction.atomic():
                employer = _find_or_create_employer(company, position)
                # Re-check the duplicate guard inside the transaction.
                if EmployerResponse.objects.filter(
                    survey=survey, employer=employer
                ).exists():
                    return render(
                        request,
                        "tracer_study/already_submitted.html",
                        {"survey": survey, "audience": "employer"},
                    )
                _save_employer_response(request, survey, employer)
        except Exception as exc:  # pragma: no cover - defensive
            import logging
            import traceback
            logging.getLogger(__name__).error(
                "Employer tracer study submit failed: %s\n%s",
                exc, traceback.format_exc(),
            )
            messages.error(
                request,
                "An error occurred while submitting your response. Please try again.",
            )
            return redirect("surveys:tracer_study_employer")

        return render(
            request,
            "tracer_study/thank_you.html",
            {"survey": survey, "audience": "employer"},
        )

    questions = survey.questions.all().prefetch_related("options")
    return render(
        request,
        "tracer_study/employer_form.html",
        {"survey": survey, "questions": questions},
    )


# ---------------------------------------------------------------------------
# Tracer Study Report
# ---------------------------------------------------------------------------
#
# A dedicated report view that aggregates the answers for the alumni or
# employer tracer study and renders them as a clean, downloadable page. The
# existing ``Report`` model is used so this report also appears in the admin
# Reports list (Report.report_type='feedback' with parameters={"survey_id": X}
# to identify it).


def _tracer_study_survey_or_404(survey_id):
    """Return the tracer study survey for the given id (or 404).

    Only the two seeded tracer study surveys are allowed — any other survey
    id returns 404 so the URL can't be used as a generic report proxy.
    """
    survey = get_object_or_404(Survey, pk=survey_id)
    if survey.title not in (ALUMNI_TITLE, EMPLOYER_TITLE):
        from django.http import Http404
        raise Http404("Not a tracer study survey.")
    return survey


SCALE_LABELS_EXTENT = {
    1: "1 - Very Low",
    2: "2 - Low",
    3: "3 - Moderate",
    4: "4 - High",
    5: "5 - Very High",
}

SCALE_LABELS_FBR = {
    1: "1 - FBR (Far Below Requirement)",
    2: "2 - BR (Below Requirement)",
    3: "3 - MR (Meeting Requirement)",
    4: "4 - AR (Above Requirement)",
    5: "5 - FBR (Far Above Requirement)",
}


def _aggregate_question(survey, question, alumni_model, employer_model):
    """Return an aggregation dict for a single question.

    Dispatches on ``question.question_type`` and uses the appropriate answer
    table (``ResponseAnswer`` for alumni, ``EmployerResponseAnswer`` for
    employer).
    """
    audience = "alumni" if survey.title == ALUMNI_TITLE else "employer"
    answer_model = ResponseAnswer if audience == "alumni" else EmployerResponseAnswer
    response_model = SurveyResponse if audience == "alumni" else EmployerResponse

    qs = answer_model.objects.filter(question=question)
    total_responses = response_model.objects.filter(survey=survey).count()

    type_label = {
        "text": "Text", "email": "Email", "number": "Number",
        "phone": "Phone", "url": "URL", "date": "Date", "time": "Time",
        "multiple_choice": "Single Choice", "checkbox": "Multiple Choice",
        "rating": "Rating", "likert": "Likert",
    }.get(question.question_type, question.question_type)

    if question.question_type in ("text", "email", "number", "phone", "url", "date", "time"):
        rows = list(
            qs.exclude(Q(text_answer__isnull=True) | Q(text_answer=""))
            .values_list("text_answer", flat=True)
        )
        return {
            "kind": "text",
            "type_label": type_label,
            "answers": rows,
            "count": len(rows),
            "total_responses": total_responses,
        }

    if question.question_type == "multiple_choice":
        option_counts = {
            o.id: o.option_text for o in question.options.all()
        }
        counts = dict(
            qs.exclude(selected_option__isnull=True)
              .values_list("selected_option_id")
              .annotate(n=Count("id"))
        )
        total = sum(counts.values()) or 0
        rows = []
        for opt_id, label in option_counts.items():
            n = counts.get(opt_id, 0)
            pct = (n / total * 100.0) if total else 0.0
            rows.append({"label": label, "count": n, "percent": pct})
        # Free-text "Other" answers
        other = list(
            qs.exclude(Q(custom_text__isnull=True) | Q(custom_text=""))
            .values_list("custom_text", flat=True)
        )
        if other:
            rows.append({"label": "Other (free text)", "count": len(other), "percent": 0.0, "other": other})
        return {
            "kind": "choice",
            "type_label": type_label,
            "rows": rows,
            "total_selections": total,
            "total_responses": total_responses,
        }

    if question.question_type == "checkbox":
        option_counts = {
            o.id: o.option_text for o in question.options.all()
        }
        counts = dict(
            qs.values_list("selected_option_id")
              .annotate(n=Count("id"))
        )
        total = sum(counts.values()) or 0
        rows = []
        for opt_id, label in option_counts.items():
            n = counts.get(opt_id, 0)
            pct = (n / total_responses * 100.0) if total_responses else 0.0
            rows.append({"label": label, "count": n, "percent": pct})
        other = list(
            qs.exclude(Q(custom_text__isnull=True) | Q(custom_text=""))
            .values_list("custom_text", flat=True)
        )
        if other:
            rows.append({"label": "Other (free text)", "count": len(other), "percent": 0.0, "other": other})
        return {
            "kind": "checkbox",
            "type_label": type_label,
            "rows": rows,
            "total_selections": total,
            "total_responses": total_responses,
        }

    if question.question_type in ("rating", "likert"):
        label_map = (
            SCALE_LABELS_EXTENT if question.scale_type == "extent" else SCALE_LABELS_FBR
        )
        buckets = {i: 0 for i in range(1, 6)}
        rating_rows = qs.exclude(rating_value__isnull=True).values_list("rating_value", flat=True)
        n = 0
        total_score = 0
        for v in rating_rows:
            if v in buckets:
                buckets[v] += 1
                n += 1
                total_score += v
        avg = (total_score / n) if n else 0.0
        rows = []
        for i in range(1, 6):
            cnt = buckets[i]
            pct = (cnt / n * 100.0) if n else 0.0
            rows.append({"label": label_map.get(i, str(i)), "count": cnt, "percent": pct})
        return {
            "kind": "rating",
            "type_label": type_label,
            "rows": rows,
            "average": avg,
            "count": n,
            "total_responses": total_responses,
        }

    return {"kind": "unknown", "type_label": type_label}


@login_required
def tracer_study_reports(request):
    """Landing page for the two tracer study reports."""
    if not _can_view_tracer_reports(request.user):
        return redirect("surveys:tracer_study_alumni")

    surveys = []
    for title, audience in ((ALUMNI_TITLE, "alumni"), (EMPLOYER_TITLE, "employer")):
        try:
            s = Survey.objects.get(title=title)
        except Survey.DoesNotExist:
            continue
        if audience == "alumni":
            count = SurveyResponse.objects.filter(survey=s).count()
        else:
            count = EmployerResponse.objects.filter(survey=s).count()
        surveys.append({"survey": s, "audience": audience, "count": count})

    return render(
        request,
        "tracer_study/reports_index.html",
        {"surveys": surveys},
    )


@login_required
def tracer_study_report(request, survey_id):
    """Aggregate report for a tracer study survey."""
    if not _can_view_tracer_reports(request.user):
        return redirect("surveys:tracer_study_alumni")

    survey = _tracer_study_survey_or_404(survey_id)
    audience = "alumni" if survey.title == ALUMNI_TITLE else "employer"

    # Upsert a Report row so this report also appears in the admin Reports
    # list and can be exported in future. parameters={"survey_id": X} is the
    # tag the existing Survey Feedback report logic uses to scope by survey.
    report, _ = Report.objects.get_or_create(
        title=f"Tracer Study Report — {audience.title()}",
        report_type="feedback",
        created_by=request.user,
        defaults={"parameters": {"survey_id": survey.id, "audience": audience}},
    )
    # Keep parameters in sync if survey_id / audience drift.
    p = report.parameters or {}
    if p.get("survey_id") != survey.id or p.get("audience") != audience:
        p["survey_id"] = survey.id
        p["audience"] = audience
        report.parameters = p
        report.save(update_fields=["parameters"])
    report.last_run = timezone.now()
    report.save(update_fields=["last_run"])

    response_model = SurveyResponse if audience == "alumni" else EmployerResponse
    total_responses = response_model.objects.filter(survey=survey).count()
    response_rows = []
    responded_rows = []
    missing_rows = []
    response_rate = None
    if audience == "alumni":
        response_rows = _alumni_response_rows(survey)
        responded_rows = [row for row in response_rows if row["submitted_at"]]
        missing_rows = [row for row in response_rows if not row["submitted_at"]]
        response_rate = (len(responded_rows) / len(response_rows) * 100) if response_rows else 0

    # Group questions by part (stored in help_text JSON)
    questions = (
        survey.questions.all()
        .prefetch_related("options")
        .order_by("display_order")
    )
    import json
    sections = []
    current = None
    for q in questions:
        try:
            meta = json.loads(q.help_text) if q.help_text else {}
        except (ValueError, TypeError):
            meta = {}
        part = meta.get("part") or ""
        if current is None or current["part"] != part:
            current = {"part": part, "questions": []}
            sections.append(current)
        agg = _aggregate_question(survey, q, SurveyResponse, EmployerResponse)
        current["questions"].append({
            "question": q,
            "aggregation": agg,
        })

    return render(
        request,
        "tracer_study/report.html",
        {
            "survey": survey,
            "audience": audience,
            "total_responses": total_responses,
            "total_expected": len(response_rows),
            "responded_rows": responded_rows,
            "missing_rows": missing_rows,
            "response_rate": response_rate,
            "sections": sections,
            "report": report,
        },
    )


@login_required
def tracer_study_report_export(request, survey_id):
    if not _can_view_tracer_reports(request.user):
        return redirect("surveys:tracer_study_alumni")

    survey = _tracer_study_survey_or_404(survey_id)
    if survey.title != ALUMNI_TITLE:
        raise Http404

    rows = _alumni_response_rows(survey)
    responded_rows = [row for row in rows if row["submitted_at"]]
    missing_rows = [row for row in rows if not row["submitted_at"]]

    from openpyxl import Workbook

    wb = Workbook()
    headers = ["Alumni ID", "Name", "Email", "Program", "Graduation Year", "Status", "Submitted At"]

    def write_sheet(ws, sheet_rows):
        ws.append(headers)
        ws.freeze_panes = "A2"
        for row in sheet_rows:
            ws.append([
                row["id"],
                row["name"],
                row["email"],
                row["course"],
                row["graduation_year"],
                row["status"],
                row["submitted_at"].strftime("%Y-%m-%d %H:%M:%S") if row["submitted_at"] else "",
            ])
        for column_cells in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 45)

    ws = wb.active
    ws.title = "Responded"
    write_sheet(ws, responded_rows)
    write_sheet(wb.create_sheet("No Response"), missing_rows)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="tracer-study-response-status.xlsx"'
    wb.save(response)
    return response
