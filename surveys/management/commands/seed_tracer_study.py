"""
Seed the NORSU Graduate Tracer Study (GTS) questionnaires.

Idempotent: re-running the command updates the existing seeded surveys in
place rather than creating duplicates. Pass --reset to delete and recreate.

Two surveys are created:

* ``NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)`` - linked to
  ``Alumni`` via ``SurveyResponse.alumni``.
* ``NORSU Graduate Tracer Study (EMPLOYER QUESTIONNAIRE)`` - linked to
  ``Employer`` via ``EmployerResponse``.

Usage::

    python manage.py seed_tracer_study
    python manage.py seed_tracer_study --reset
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from surveys.models import (
    Survey, SurveyQuestion, QuestionOption, Employer,
)

User = get_user_model()


ALUMNI_TITLE = "NORSU Graduate Tracer Study (ALUMNI QUESTIONNAIRE)"
EMPLOYER_TITLE = "NORSU Graduate Tracer Study (EMPLOYER QUESTIONNAIRE)"


ALUMNI_DESCRIPTION = (
    "A Graduate Tracer Study (GTS) for profiling of NORSU graduates and "
    "research purposes to assess employability and improve course offerings. "
    "Conducted by the Alumni Affairs Office in line with the Data Privacy "
    "Act of 2012. For questions, contact norsualumniaffairsoffice@norsu.edu.ph."
)

EMPLOYER_DESCRIPTION = (
    "Companion employer questionnaire to the NORSU Graduate Tracer Study. "
    "Rate the job performance of NORSU graduates employed by your organization. "
    "Conducted by the Alumni Affairs Office in line with the Data Privacy "
    "Act of 2012."
)


YES_NO_OTHER = [
    ("yes", "Yes", False),
    ("no", "No", False),
    ("never", "Never Employed", False),
    ("other", "Other (please specify)", True),
]


CAMPUS_CHOICES = [
    ("main1", "Main Campus I"),
    ("main2", "Main Campus II"),
    ("bayawan", "Bayawan-Sta. Catalina Campus"),
    ("siaton", "Siaton Campus"),
    ("guihulngan", "Guihulngan Campus"),
    ("bais", "Bais Campuses"),
    ("mabinay", "Mabinay Campus"),
    ("pamplona", "Pamplona Campus"),
]


def mc(ordered_options, allow_custom_label=None):
    """Build a QuestionOption list for a single-select multiple choice.

    ``ordered_options`` is a list of (value, label, allow_custom) tuples, or
    a plain list of (value, label) tuples (allow_custom defaults to False).
    """
    out = []
    for i, item in enumerate(ordered_options):
        if len(item) == 2:
            value, label = item
            allow_custom = False
        else:
            value, label, allow_custom = item
        out.append({
            "option_text": label,
            "display_order": i,
            "value_key": value,
            "allow_custom": allow_custom,
        })
    return out


def mc_raw(labels):
    return [{"option_text": l, "display_order": i, "value_key": l.lower(),
             "allow_custom": False} for i, l in enumerate(labels)]


def cb(ordered_options):
    """Build a QuestionOption list for a checkbox (multi-select)."""
    out = []
    for i, item in enumerate(ordered_options):
        if len(item) == 2:
            value, label = item
            allow_custom = False
        else:
            value, label, allow_custom = item
        out.append({
            "option_text": label,
            "display_order": i,
            "value_key": value,
            "allow_custom": allow_custom,
        })
    return out


def likert5_extent():
    return mc([
        ("5", "5 - Very High"),
        ("4", "4 - High"),
        ("3", "3 - Moderate"),
        ("2", "2 - Low"),
        ("1", "1 - Very Low"),
    ])


# -----------------------------------------------------------------------------
# Questionnaire definitions
# -----------------------------------------------------------------------------

ALUMNI_QUESTIONS = [
    # PART I - Personal Information
    {
        "key": "p1_name",
        "part": "PART I - Personal Information",
        "text": "Name of Respondent",
        "type": "text",
        "required": False,
        "options": [],
    },
    {
        "key": "p1_address",
        "part": "PART I - Personal Information",
        "text": "Current/Permanent Address",
        "type": "text",
        "required": False,
        "multiline": True,
        "options": [],
    },
    {
        "key": "p1_email",
        "part": "PART I - Personal Information",
        "text": "Email Address",
        "type": "email",
        "required": False,
        "options": [],
    },
    {
        "key": "p1_contact",
        "part": "PART I - Personal Information",
        "text": "Contact Number (Mobile)",
        "type": "phone",
        "required": False,
        "options": [],
    },
    {
        "key": "p1_dob",
        "part": "PART I - Personal Information",
        "text": "Date of Birth",
        "type": "date",
        "required": False,
        "options": [],
    },
    {
        "key": "p1_gender",
        "part": "PART I - Personal Information",
        "text": "Gender",
        "type": "multiple_choice",
        "required": False,
        "options": mc([
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other (please specify)", True),
        ]),
    },
    {
        "key": "p1_marital",
        "part": "PART I - Personal Information",
        "text": "Marital Status",
        "type": "multiple_choice",
        "required": False,
        "options": mc([
            ("single", "Single"),
            ("married", "Married"),
            ("other", "Other (please specify)", True),
        ]),
    },
    {
        "key": "p1_fb",
        "part": "PART I - Personal Information",
        "text": "Facebook Account",
        "type": "url",
        "required": False,
        "options": [],
    },
    {
        "key": "p1_twitter",
        "part": "PART I - Personal Information",
        "text": "Twitter Account",
        "type": "url",
        "required": False,
        "options": [],
    },

    # PART II - Educational Background
    {
        "key": "p2_course",
        "part": "PART II - Educational Background",
        "text": "Course and Major taken (Baccalaureate Degree at NORSU)",
        "type": "text",
        "required": True,
        "options": [],
    },
    {
        "key": "p2_year",
        "part": "PART II - Educational Background",
        "text": "Year Graduated",
        "type": "number",
        "required": True,
        "min": 1950,
        "max": 2100,
        "options": [],
    },
    {
        "key": "p2_campus",
        "part": "PART II - Educational Background",
        "text": "Campus",
        "type": "multiple_choice",
        "required": True,
        "options": mc([(c[0], c[1]) for c in CAMPUS_CHOICES]),
    },
    {
        "key": "p2_honors",
        "part": "PART II - Educational Background",
        "text": "Honor(s) or Awards Received (select all that apply)",
        "type": "checkbox",
        "required": False,
        "options": cb([
            ("academic", "Academic Honor (e.g. Cum Laude etc.)"),
            ("leadership", "Leadership Award"),
            ("special", "Special Academic Award"),
            ("other", "Other Awards (please specify)", True),
        ]),
    },
    {
        "key": "p2_exam_name",
        "part": "PART II - Educational Background",
        "text": "Professional Examination / National Certification passed - Name",
        "type": "text",
        "required": False,
        "multiline": True,
        "options": [],
    },
    {
        "key": "p2_exam_year",
        "part": "PART II - Educational Background",
        "text": "Professional Examination / National Certification passed - Year",
        "type": "number",
        "required": False,
        "min": 1950,
        "max": 2100,
        "options": [],
    },

    # PART III - Employment Data
    {
        "key": "p3_employed",
        "part": "PART III - Employment Data",
        "text": "Are you presently employed?",
        "type": "multiple_choice",
        "required": True,
        "options": mc([
            ("yes", "Yes"),
            ("no", "No"),
            ("never", "Never Employed"),
            ("other", "Other (please specify)", True),
        ]),
        # Conditional logic handled in template via data-conditional-on.
        "conditional": "show_if_not_employed:hide_if_employed",
    },
    {
        "key": "p3_reasons_unemployed",
        "part": "PART III - Employment Data",
        "text": "Reasons why not employed (select all that apply)",
        "type": "checkbox",
        "required": False,
        "options": cb([
            ("study", "Further study"),
            ("experience", "Lack of work experience"),
            ("family", "Family concern"),
            ("no_opportunity", "No job opportunity"),
            ("health", "Health-related reason"),
            ("no_look", "Did not look for job"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["no", "never"]},
    },
    {
        "key": "p3_status",
        "part": "PART III - Employment Data",
        "text": "Present Employment Status",
        "type": "multiple_choice",
        "required": False,
        "options": mc([
            ("regular", "Regular / Permanent"),
            ("contractual", "Contractual"),
            ("temporary", "Temporary"),
            ("self", "Self-employed"),
            ("casual", "Casual"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_position",
        "part": "PART III - Employment Data",
        "text": "Occupation / Position",
        "type": "text",
        "required": False,
        "options": [],
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_company",
        "part": "PART III - Employment Data",
        "text": "Company",
        "type": "text",
        "required": False,
        "options": [],
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_company_address",
        "part": "PART III - Employment Data",
        "text": "Company Address",
        "type": "text",
        "required": False,
        "multiline": True,
        "options": [],
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_org_type",
        "part": "PART III - Employment Data",
        "text": "Type of Organization",
        "type": "multiple_choice",
        "required": False,
        "options": mc([("government", "Government"), ("private", "Private")]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_place",
        "part": "PART III - Employment Data",
        "text": "Place of Work",
        "type": "multiple_choice",
        "required": False,
        "options": mc([("local", "Local"), ("abroad", "Abroad")]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_first_job",
        "part": "PART III - Employment Data",
        "text": "Is this your first job after college?",
        "type": "multiple_choice",
        "required": False,
        "options": mc([("yes", "Yes"), ("no", "No")]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_reasons_stay",
        "part": "PART III - Employment Data",
        "text": "Reasons for staying in job (select all that apply)",
        "type": "checkbox",
        "required": False,
        "options": cb([
            ("salary", "Salaries and benefits"),
            ("proximity", "Proximity to residence"),
            ("challenge", "Career challenge"),
            ("peer", "Peer influence"),
            ("skill", "Related to special skill"),
            ("family", "Family influence"),
            ("course", "Related to course"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_related_course",
        "part": "PART III - Employment Data",
        "text": "Is your first job related to your course?",
        "type": "multiple_choice",
        "required": False,
        "options": mc([("yes", "Yes"), ("no", "No")]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_reasons_accept",
        "part": "PART III - Employment Data",
        "text": "Reasons for accepting job (select all that apply)",
        "type": "checkbox",
        "required": False,
        "options": cb([
            ("salary", "Salaries and benefits"),
            ("skill", "Related to special skills"),
            ("challenge", "Career challenge"),
            ("proximity", "Proximity to residence"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_reasons_change",
        "part": "PART III - Employment Data",
        "text": "Reasons for changing jobs (select all that apply)",
        "type": "checkbox",
        "required": False,
        "options": cb([
            ("salary", "Salaries and benefits"),
            ("skill", "Related to special skills"),
            ("challenge", "Career challenge"),
            ("proximity", "Proximity to residence"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_first_job_duration",
        "part": "PART III - Employment Data",
        "text": "How long did you stay in your first job?",
        "type": "multiple_choice",
        "required": False,
        "options": mc([
            ("lt_1m", "Less than a month"),
            ("1_6m", "1-6 months"),
            ("7_11m", "7-11 months"),
            ("1_2y", "1-2 years"),
            ("2_3y", "2-3 years"),
            ("3_4y", "3-4 years"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_find_first_job",
        "part": "PART III - Employment Data",
        "text": "How did you find your first job?",
        "type": "multiple_choice",
        "required": False,
        "options": mc([
            ("ad", "Advertisement"),
            ("school", "School job placement officer"),
            ("walkin", "Walk-in applicant"),
            ("family_biz", "Family business"),
            ("referral", "Recommended by someone"),
            ("jobfair", "Job fair / PESO"),
            ("friends", "Friends"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_time_to_first_job",
        "part": "PART III - Employment Data",
        "text": "Time to land first job",
        "type": "multiple_choice",
        "required": False,
        "options": mc([
            ("lt_1m", "Less than a month"),
            ("1_6m", "1-6 months"),
            ("7_11m", "7-11 months"),
            ("1_2y", "1-2 years"),
            ("2_3y", "2-3 years"),
            ("3_4y", "3-4 years"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_curriculum_relevant",
        "part": "PART III - Employment Data",
        "text": "Was the curriculum relevant to your job?",
        "type": "multiple_choice",
        "required": False,
        "options": mc([("yes", "Yes"), ("no", "No")]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_useful_competencies",
        "part": "PART III - Employment Data",
        "text": "Useful competencies (select all that apply)",
        "type": "checkbox",
        "required": False,
        "options": cb([
            ("communication", "Communication skills"),
            ("problem", "Problem-solving skills"),
            ("human", "Human relations skills"),
            ("critical", "Critical thinking skills"),
            ("entrepreneurial", "Entrepreneurial skills"),
            ("other", "Other (please specify)", True),
        ]),
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_apply_learning",
        "part": "PART III - Employment Data",
        "text": "How do you apply university learning?",
        "type": "text",
        "required": False,
        "multiline": True,
        "options": [],
        "show_when": {"p3_employed": ["yes"]},
    },
    {
        "key": "p3_suggestions",
        "part": "PART III - Employment Data",
        "text": "Suggestions for improvement",
        "type": "text",
        "required": False,
        "multiline": True,
        "options": [],
    },

    # PART IV - Extent of Manifestation (5 items, extent scale)
    {
        "key": "p4_vision",
        "part": "PART IV - Extent of Manifestation",
        "text": "Vision (Extent of manifestation in your professional practice)",
        "type": "rating",
        "scale_type": "extent",
        "required": False,
        "options": likert5_extent(),
    },
    {
        "key": "p4_mission",
        "part": "PART IV - Extent of Manifestation",
        "text": "Mission (Extent of manifestation in your professional practice)",
        "type": "rating",
        "scale_type": "extent",
        "required": False,
        "options": likert5_extent(),
    },
    {
        "key": "p4_goals",
        "part": "PART IV - Extent of Manifestation",
        "text": "Goals (Extent of manifestation in your professional practice)",
        "type": "rating",
        "scale_type": "extent",
        "required": False,
        "options": likert5_extent(),
    },
    {
        "key": "p4_core_values",
        "part": "PART IV - Extent of Manifestation",
        "text": "Core Values (Extent of manifestation in your professional practice)",
        "type": "rating",
        "scale_type": "extent",
        "required": False,
        "options": likert5_extent(),
    },
    {
        "key": "p4_program_objectives",
        "part": "PART IV - Extent of Manifestation",
        "text": "Program Objectives (Extent of manifestation in your professional practice)",
        "type": "rating",
        "scale_type": "extent",
        "required": False,
        "options": likert5_extent(),
    },
]


EXTENT_FAR_FBR = mc([
    ("5", "5 - FAR"),
    ("4", "4 - AR"),
    ("3", "3 - MR"),
    ("2", "2 - BR"),
    ("1", "1 - FBR"),
])


EMPLOYER_QUESTIONS = [
    # PART I - General Information
    {
        "key": "emp_company_name",
        "part": "PART I - General Information",
        "text": "Company Name",
        "type": "text",
        "required": True,
        "options": [],
    },
    {
        "key": "emp_position",
        "part": "PART I - General Information",
        "text": "Position",
        "type": "text",
        "required": True,
        "options": [],
    },
    {
        "key": "emp_address",
        "part": "PART I - General Information",
        "text": "Address",
        "type": "text",
        "required": False,
        "options": [],
    },
    {
        "key": "emp_place",
        "part": "PART I - General Information",
        "text": "Place of Company",
        "type": "text",
        "required": False,
        "options": [],
    },

    # PART II - Job Performance - Attitude and Values
    {
        "key": "att_individual",
        "part": "Attitude and Values",
        "text": "Individual Values",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "att_professional",
        "part": "Attitude and Values",
        "text": "Professional Values",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "att_commercial",
        "part": "Attitude and Values",
        "text": "Commercial Attitude",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "att_self",
        "part": "Attitude and Values",
        "text": "Self-management",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "att_digital",
        "part": "Attitude and Values",
        "text": "Digital literacy",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },

    # Skills
    {
        "key": "sk_transferable",
        "part": "Skills",
        "text": "Transferable skills",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "sk_communication",
        "part": "Skills",
        "text": "Communication skills",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "sk_technical",
        "part": "Skills",
        "text": "Technical skills",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "sk_general",
        "part": "Skills",
        "text": "General skills",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "sk_manual",
        "part": "Skills",
        "text": "Manual skills",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },

    # Knowledge
    {
        "key": "kn_job",
        "part": "Knowledge",
        "text": "Job knowledge",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "kn_critical",
        "part": "Knowledge",
        "text": "Critical thinking",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "kn_problem",
        "part": "Knowledge",
        "text": "Problem solving",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },
    {
        "key": "kn_work_habits",
        "part": "Knowledge",
        "text": "Work habits",
        "type": "rating", "scale_type": "extent", "required": False,
        "options": EXTENT_FAR_FBR,
    },

    # Open comment
    {
        "key": "open_comment",
        "part": "Open Comment",
        "text": "Comments or suggestions",
        "type": "text",
        "required": False,
        "options": [],
    },
]


# -----------------------------------------------------------------------------
# Seeder helpers
# -----------------------------------------------------------------------------

def _get_or_create_survey(title, description, created_by):
    survey, created = Survey.objects.get_or_create(
        title=title,
        defaults={
            "description": description,
            "start_date": timezone.now() - timedelta(days=1),
            "end_date": timezone.now() + timedelta(days=365),
            "status": "active",
            "created_by": created_by,
            "is_external": False,
        },
    )
    if not created:
        survey.description = description
        survey.status = "active"
        survey.start_date = timezone.now() - timedelta(days=1)
        survey.end_date = timezone.now() + timedelta(days=365)
        survey.save(update_fields=["description", "status", "start_date", "end_date"])
    return survey


def _apply_questions(survey, question_defs):
    """Replace survey.questions with the given definitions.

    Stores the source ``key`` and ``conditional`` info in ``help_text`` as
    JSON so the take_survey template can render conditional groups without
    needing a database migration for that.

    The ``show_when`` map is built in two passes: pass 1 creates the
    questions (collecting key -> id), pass 2 rewrites help_text with the
    show_when keys converted to integer question ids. The form's JS reads
    ``data-conditional-on`` and looks up radios by
    ``input[name="question_<id>"]:checked``, so the keys must be ids.
    """
    import json

    with transaction.atomic():
        survey.questions.all().delete()

        # Pass 1: create all questions; show_when is left empty for now.
        created = {}        # key -> SurveyQuestion
        part_for_key = {}   # key -> part label
        order = 0
        for qd in question_defs:
            question = SurveyQuestion.objects.create(
                survey=survey,
                question_text=qd["text"],
                question_type=qd["type"],
                is_required=qd.get("required", False),
                display_order=order,
                scale_type=qd.get("scale_type") or "",
                help_text=json.dumps({
                    "key": qd["key"],
                    "part": qd.get("part", ""),
                    "show_when": {},
                    "multiline": bool(qd.get("multiline", False)),
                    "min": qd.get("min"),
                    "max": qd.get("max"),
                }),
            )
            for opt in qd.get("options", []):
                QuestionOption.objects.create(
                    question=question,
                    option_text=opt["option_text"],
                    display_order=opt["display_order"],
                    allow_custom=opt.get("allow_custom", False),
                )
            created[qd["key"]] = question
            part_for_key[qd["key"]] = qd.get("part", "")
            order += 1

    # Pass 2: rewrite show_when with resolved question ids.
    updates = []
    for qd in question_defs:
        raw = qd.get("show_when") or {}
        if not raw:
            continue
        resolved = {}
        for trigger_key, allowed in raw.items():
            trigger_q = created.get(trigger_key)
            if trigger_q is not None:
                resolved[str(trigger_q.id)] = allowed
        if not resolved:
            continue
        question = created[qd["key"]]
        meta = json.loads(question.help_text) if question.help_text else {}
        meta["show_when"] = resolved
        question.help_text = json.dumps(meta)
        updates.append(question)

    if updates:
        SurveyQuestion.objects.bulk_update(updates, ["help_text"])


class Command(BaseCommand):
    help = "Seed the NORSU Graduate Tracer Study (Alumni + Employer) surveys."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seeded tracer study surveys before recreating.",
        )

    def handle(self, *args, **options):
        created_by = self._get_creator()
        if options["reset"]:
            Survey.objects.filter(title__in=[ALUMNI_TITLE, EMPLOYER_TITLE]).delete()
            self.stdout.write(self.style.WARNING("Existing tracer study surveys deleted."))

        alumni = _get_or_create_survey(ALUMNI_TITLE, ALUMNI_DESCRIPTION, created_by)
        _apply_questions(alumni, ALUMNI_QUESTIONS)
        self.stdout.write(self.style.SUCCESS(
            f"Alumni survey: {alumni.questions.count()} questions seeded."
        ))

        employer = _get_or_create_survey(EMPLOYER_TITLE, EMPLOYER_DESCRIPTION, created_by)
        _apply_questions(employer, EMPLOYER_QUESTIONS)
        self.stdout.write(self.style.SUCCESS(
            f"Employer survey: {employer.questions.count()} questions seeded."
        ))

    @staticmethod
    def _get_creator():
        creator = User.objects.filter(is_superuser=True).first()
        if creator is None:
            creator = User.objects.filter(is_staff=True).first()
        if creator is None:
            creator = User.objects.first()
        return creator
