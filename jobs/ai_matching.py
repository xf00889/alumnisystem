"""
AI-powered job matching using Google Gemini API.

Analyzes a user's skills, education, and experience against a job posting
and returns a match score with strengths and gaps.
"""

import json
import re
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def _get_gemini_client():
    """
    Return (client, model_name) using the new google-genai SDK from DB config.
    Returns (None, None) if unavailable.
    """
    try:
        from core.ai_config_utils import get_gemini_client
        return get_gemini_client()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client from DB config: {e}")
        return None, None


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
                import datetime
                end = e.end_date or datetime.date.today()
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


def _extract_text_from_response(response):
    """
    Safely extract text from a Gemini response object.
    Handles both standard and thinking model response structures.
    """
    # Try response.text first (works for most models)
    try:
        if response.text:
            return response.text
    except Exception:
        pass

    # For thinking models: iterate candidates -> content -> parts
    try:
        for candidate in (response.candidates or []):
            content = getattr(candidate, 'content', None)
            if not content:
                continue
            parts = getattr(content, 'parts', []) or []
            text_parts = []
            for part in parts:
                t = getattr(part, 'text', None)
                if t:
                    text_parts.append(t)
            if text_parts:
                return ''.join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from candidates: {e}")

    return ""


def _extract_json(text):
    """
    Robustly extract a JSON object from a string that may contain
    markdown fences, thinking text, or other surrounding content.
    """
    if not text:
        return None

    # 1. Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 2. Strip ```json ... ``` or ``` ... ``` fences
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Find the LAST { ... } block (thinking models put reasoning first)
    brace_matches = list(re.finditer(r'\{[\s\S]*?\}', text))
    for m in reversed(brace_matches):
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            continue

    # 4. Find the largest { ... } block spanning the whole JSON
    start = text.rfind('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


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
    # Check cache first (24 hours to save API calls)
    cache_key = f"ai_match_{user.id}_{job.id}"
    cached = cache.get(cache_key)
    if cached:
        cached['cached'] = True
        return cached

    client, model_name = _get_gemini_client()
    if not client:
        return _fallback_result("AI matching is currently unavailable. Please configure an AI API key in the admin dashboard.")

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

You MUST respond with ONLY a valid JSON object. No explanation, no markdown, no code fences.
Use this exact structure:
{{"score": 75, "reason": "One sentence summary.", "strengths": ["strength 1", "strength 2"], "gaps": ["gap 1"]}}

Scoring guide:
- 80-100: Excellent match
- 60-79: Good match with minor gaps
- 40-59: Moderate match with notable gaps
- 20-39: Weak match
- 0-19: Poor match
"""

    raw = ""
    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
            )
        )

        # Safely get text using robust extractor
        raw = _extract_text_from_response(response)

        logger.debug(f"Gemini raw response for user={user.id}, job={job.id}: {raw[:500]}")

        if not raw:
            logger.error(f"Gemini returned empty response for user={user.id}, job={job.id}")
            return _fallback_result("AI returned an empty response.")

        result = _extract_json(raw)

        if result is None:
            logger.error(f"Could not extract JSON from Gemini response: {raw[:300]}")
            return _fallback_result("AI returned an unexpected response format.")

        # Validate and clamp
        result['score'] = max(0, min(100, int(result.get('score', 0))))
        result['strengths'] = result.get('strengths', [])[:5]
        result['gaps'] = result.get('gaps', [])[:5]
        result['reason'] = result.get('reason', '')
        result['cached'] = False

        # Cache for 24 hours
        cache.set(cache_key, result, 60 * 60 * 24)

        logger.info(f"AI match score: user={user.id}, job={job.id}, score={result['score']}")
        return result

    except Exception as e:
        logger.error(f"Gemini API error for user={user.id}, job={job.id}: {e}\nRaw: {raw[:200]}")
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
