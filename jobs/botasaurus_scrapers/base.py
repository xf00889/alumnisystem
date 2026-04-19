"""
Base utilities shared across all botasaurus job scrapers.
"""
import re
import logging

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Strip and collapse whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())

def normalize_description(text: str) -> str:
    """
    Clean job descriptions with minimal transformation.
    Keep formatting stable and only remove known scraper junk.
    """
    if not text:
        return ""

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Drop known prompt-template lead-ins, e.g.
    # "Tips: Provide a summary of the role..."
    cleaned = re.sub(
        r"^\s*tips:\s*provide a summary of the role.*?(?=\b(responsibilities|job responsibilities|qualifications|job qualifications|requirements)\b)",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Keep readable spacing, avoid single-line walls.
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    lines = [re.sub(r"\s+", " ", line).strip() for line in cleaned.split("\n")]
    cleaned = "\n".join(line for line in lines if line)

    return cleaned.strip()


def is_meaningful_description(text: str) -> bool:
    """Reject metadata-like or too-short snippets as job descriptions."""
    if not text:
        return False
    t = normalize_description(text)
    low = t.lower()
    if len(t) < 80:
        return False
    if "be an early applicant" in low:
        return False
    if "hours ago" in low and len(t) < 220:
        return False
    if "posted" in low and "ago" in low and len(t) < 220:
        return False
    # Need enough words to be a real description.
    if len(re.findall(r"[A-Za-z]{3,}", t)) < 18:
        return False
    return True


def clean_salary(text: str) -> str:
    """Return a cleaned salary string, or empty string if not useful."""
    if not text:
        return ""
    cleaned = normalize_text(text)
    # Drop placeholder strings
    if cleaned.lower() in {"salary not disclosed", "not disclosed", "n/a", "tbd", "negotiable"}:
        return cleaned
    return cleaned


def build_job_dict(
    title: str,
    company: str,
    location: str,
    description: str = "",
    salary: str = "",
    job_type: str = "",
    url: str = "",
    source: str = "",
) -> dict:
    """Return a normalised job dictionary."""
    return {
        "title": normalize_text(title) or "Job Title Not Available",
        "company": normalize_text(company) or "Company Not Specified",
        "location": normalize_text(location) or "Location Not Specified",
        "description": normalize_description(description),
        "salary": clean_salary(salary),
        "job_type": normalize_text(job_type),
        "url": url or "",
        "source": source,
    }


def make_empty_result(keyword: str, location: str, source: str, error: str) -> dict:
    """Return a standard failure result dict."""
    return {
        "success": False,
        "jobs": [],
        "total_found": 0,
        "keyword": keyword,
        "location": location,
        "source": source,
        "error": error,
        "message": error,
    }


def make_success_result(keyword: str, location: str, source: str, jobs: list) -> dict:
    """Return a standard success result dict."""
    return {
        "success": True,
        "jobs": jobs,
        "total_found": len(jobs),
        "keyword": keyword,
        "location": location,
        "source": source,
        "message": f"Found {len(jobs)} job(s) for '{keyword}' in '{location}' from {source}",
    }
