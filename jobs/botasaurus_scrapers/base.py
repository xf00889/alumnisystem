"""
Base utilities shared across all botasaurus job scrapers.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Strip and collapse whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


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
        "description": normalize_text(description),
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
