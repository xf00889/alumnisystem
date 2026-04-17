"""
AI-powered job matching using Google Gemini API.

Analyzes a user's skills, education, and experience against a job posting
and returns a match score with strengths and gaps.
"""

import json
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def _get_gemini_client():
    """Initialize and return the Gemini generative model."""
    try:
        import google.generativeai as genai
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            logger.warning("GEMINI_API_KEY is not set in settings.")
            return None
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash")
    except ImportError:
        logger.error("google-generativeai package is not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None


def build_user_profile(user):
    """Extract relevant profile data for AI matching."""
    try:
        profile = user.profile

        # Skills
        skills = [
            f"{s.name} ({s.get_proficiency_level_display()}, {s.years_of_experience} yrs)"
            for s in profile.skills.all()[:20]
        ]

        # Education
        education = []
        for e in profile.education.all():
            parts = []
            if e.program:
                parts.append(e.get_program_display())
            if e.school:
                parts.append(e.get_school_display())
            if e.graduation_year:
                parts.append(str(e.graduation_year))
            if parts:
                education.append(", ".join(parts))

        # Experience
        experience = []
        for e in profile.experience.all()[:10]:
            duration = ""
            if e.start_date:
                end = e.end_date or __import__('datetime').date.today()
                months = (end.year - e.start_date.year) * 12 + (end.month - e.start_date.month)
                duration = f"{months // 12}y {months % 12}m"
            experience.append(
                f"{e.position} at {e.company} ({duration})"
                + (f" — {e.description[:100]}" if e.description else "")
            )

        return {
            "current_position": profile.current_position or "",
            "current_employer": profile.current_employer or "",
            "employment_status": profile.get_employment_status_display() if profile.employment_status else "",
            "skills": skills,
            "education": education,
            "experience": experience,
            "bio": (profile.bio or "")[:200],
        }
    except Exception as e:
        logger.error(f"Error building user profile for AI matching: {e}")
        return {}


def build_job_summary(job):
    """Extract relevant job data for AI matching."""
    return {
        "title": job.job_title,
        "company": job.company_name,
        "location": job.location,
        "job_type": job.get_job_type_display(),
        "experience_level": job.get_experience_level_display(),
        "description": (job.job_description or "")[:500],
        "requirements": (job.requirements or "")[:500],
        "skills_required": job.skills_required or "",
        "education_requirements": job.education_requirements or "",
    }


def get_ai_match_score(user, job):
    """
    Use Google Gemini to score how well a user matches a job posting.

    Returns a dict:
    {
        "score": int (0-100),
        "reason": str,
        "strengths": list[str],
        "gaps": list[str],
        "cached": bool
    }
    Falls back gracefully if the API is unavailable.
    """
    # Check cache first (cache for 24 hours to save API calls)
    cache_key = f"ai_match_{user.id}_{job.id}"
    cached = cache.get(cache_key)
    if cached:
        cached['cached'] = True
        return cached

    model = _get_gemini_client()
    if not model:
        return _fallback_result("AI matching is currently unavailable.")

    user_data = build_user_profile(user)
    job_data = build_job_summary(job)

    if not user_data:
        return _fallback_result("Could not load your profile data.")

    prompt = f"""You are a professional job matching assistant for a university alumni system.
Analyze how well this candidate matches the job posting and provide a realistic assessment.

CANDIDATE PROFILE:
{json.dumps(user_data, indent=2)}

JOB POSTING:
{json.dumps(job_data, indent=2)}

Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{{
  "score": <integer 0-100>,
  "reason": "<one concise sentence summarizing the overall match>",
  "strengths": ["<specific strength 1>", "<specific strength 2>", "<specific strength 3>"],
  "gaps": ["<specific gap 1>", "<specific gap 2>"]
}}

Scoring guide:
- 80-100: Excellent match, candidate meets most/all requirements
- 60-79: Good match, candidate meets core requirements with minor gaps
- 40-59: Moderate match, some relevant experience but notable gaps
- 20-39: Weak match, limited relevant experience
- 0-19: Poor match, significant skill/experience mismatch
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 400,
            }
        )

        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        result = json.loads(raw)

        # Validate and clamp score
        result['score'] = max(0, min(100, int(result.get('score', 0))))
        result['strengths'] = result.get('strengths', [])[:5]
        result['gaps'] = result.get('gaps', [])[:5]
        result['reason'] = result.get('reason', '')
        result['cached'] = False

        # Cache for 24 hours
        cache.set(cache_key, result, 60 * 60 * 24)

        logger.info(f"AI match score computed: user={user.id}, job={job.id}, score={result['score']}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON for user={user.id}, job={job.id}: {e}\nRaw: {raw[:200]}")
        return _fallback_result("AI returned an unexpected response.")
    except Exception as e:
        logger.error(f"Gemini API error for user={user.id}, job={job.id}: {e}")
        return _fallback_result("AI matching service is temporarily unavailable.")


def _fallback_result(reason):
    """Return a safe fallback when AI matching fails."""
    return {
        "score": None,
        "reason": reason,
        "strengths": [],
        "gaps": [],
        "cached": False,
        "error": True,
    }
