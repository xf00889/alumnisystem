"""
Utilities for converting scraped job dicts into JobPosting records.
Used by the Django admin to publish scraped jobs to the job board.
"""
import logging
import re
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import JobPosting, ScrapedJob

logger = logging.getLogger(__name__)
User = get_user_model()

# Map ScrapedJob source keys → JobPosting.source value
SOURCE_LABEL_MAP = {
    "JOBSTREET":  "jobstreet",
    "INDEED":     "indeed",
    "LINKEDIN":   "linkedin",
    "KALIBRR":    "kalibrr",
    "BOSSJOB":    "bossjob",
    "PHILJOBNET": "philjobnet",
    "ONLINEJOBS": "onlinejobs",
    "JORA":       "jora",
    "MYNIMO":     "mynimo",
    "WORKABROAD": "workabroad",
    "OTHER":      "other",
}

# Keyword → category heuristic
CATEGORY_KEYWORDS = {
    "technology":      ["developer", "engineer", "programmer", "software", "it ", "tech", "data", "devops", "cloud", "cyber", "network", "system", "web", "mobile", "qa", "tester"],
    "finance":         ["accountant", "accounting", "finance", "auditor", "bookkeeper", "payroll", "tax", "treasury", "cpa", "financial"],
    "healthcare":      ["nurse", "doctor", "physician", "medical", "health", "pharmacist", "therapist", "dentist", "clinical", "hospital"],
    "education":       ["teacher", "instructor", "professor", "tutor", "trainer", "faculty", "academic", "school", "university"],
    "sales_marketing": ["sales", "marketing", "brand", "digital marketing", "seo", "social media", "account manager", "business development"],
    "hospitality":     ["hotel", "restaurant", "chef", "cook", "barista", "waiter", "tourism", "travel", "hospitality"],
    "manufacturing":   ["production", "manufacturing", "assembly", "quality control", "warehouse", "logistics", "supply chain", "operator"],
    "administrative":  ["admin", "secretary", "receptionist", "clerk", "office", "data entry", "virtual assistant", "executive assistant"],
    "construction":    ["engineer", "architect", "construction", "civil", "structural", "project manager", "site"],
    "creative":        ["designer", "graphic", "artist", "creative", "photographer", "videographer", "animator", "ux", "ui"],
}


def guess_category(title: str, description: str = "") -> str:
    """Guess the job category from title and description."""
    text = (title + " " + description).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "other"


def guess_job_type(title: str, description: str = "", job_type_raw: str = "") -> str:
    """Map raw job type string to JobPosting.JOB_TYPE_CHOICES key."""
    raw = (job_type_raw + " " + title + " " + description).lower()
    if "part" in raw and "time" in raw:
        return "PART_TIME"
    if "contract" in raw or "freelance" in raw or "project-based" in raw:
        return "CONTRACT"
    if "remote" in raw or "work from home" in raw or "wfh" in raw:
        return "REMOTE"
    if "intern" in raw or "ojt" in raw or "on-the-job" in raw:
        return "INTERNSHIP"
    return "FULL_TIME"


def guess_experience_level(title: str, description: str = "") -> str:
    """Guess experience level from title/description."""
    text = (title + " " + description).lower()
    if any(kw in text for kw in ["senior", "sr.", "lead", "principal", "head of", "director", "vp", "vice president"]):
        return "SENIOR"
    if any(kw in text for kw in ["executive", "ceo", "cto", "cfo", "c-level", "president"]):
        return "EXECUTIVE"
    if any(kw in text for kw in ["mid", "intermediate", "associate"]):
        return "MID"
    return "ENTRY"


def scraped_job_dict_to_posting(
    job_dict: dict,
    source_key: str,
    posted_by: User,
    is_featured: bool = False,
) -> Optional[JobPosting]:
    """
    Convert a single scraped job dict into a JobPosting instance.
    Returns None if the job is a duplicate (same title + company already exists).
    Does NOT save — caller must call .save() or use bulk_create.
    """
    title = (job_dict.get("title") or "").strip()
    company = (job_dict.get("company") or "").strip()
    location = (job_dict.get("location") or "Philippines").strip()
    description = (job_dict.get("description") or "").strip()
    salary = (job_dict.get("salary") or "").strip()
    job_type_raw = (job_dict.get("job_type") or "").strip()
    url = (job_dict.get("url") or "").strip()

    if not title or title.lower() == "job title not available":
        return None

    # Deduplication: skip if a posting with same title+company already exists
    if JobPosting.objects.filter(
        job_title__iexact=title,
        company_name__iexact=company,
        is_active=True,
    ).exists():
        logger.debug(f"Skipping duplicate: '{title}' at '{company}'")
        return None

    source_value = SOURCE_LABEL_MAP.get(source_key, "other")
    category = guess_category(title, description)
    job_type = guess_job_type(title, description, job_type_raw)
    experience_level = guess_experience_level(title, description)

    posting = JobPosting(
        job_title=title,
        company_name=company or "Unknown Company",
        location=location,
        job_type=job_type,
        job_description=description or f"View full job details at the source: {url}",
        experience_level=experience_level,
        salary_range=salary or None,
        application_link=url if url and url.startswith("http") else None,
        source=source_value,
        source_type="EXTERNAL",
        category=category,
        is_featured=is_featured,
        is_active=True,
        posted_by=posted_by,
        accepts_internal_applications=False,
    )
    return posting


def publish_scraped_job(scraped_job: ScrapedJob, posted_by: User) -> dict:
    """
    Convert all jobs in a ScrapedJob record into JobPosting records.

    Returns a summary dict:
        {
            "published": int,   # new postings created
            "skipped":   int,   # duplicates skipped
            "errors":    int,   # jobs that failed
        }
    """
    summary = {"published": 0, "skipped": 0, "errors": 0}
    source_key = scraped_job.source

    jobs_data = scraped_job.jobs_data
    if not jobs_data:
        # Try to get jobs from the nested result dict
        raw = scraped_job.scraped_data
        if isinstance(raw, dict):
            jobs_data = raw.get("jobs", [])

    postings_to_create = []

    for job_dict in jobs_data:
        try:
            posting = scraped_job_dict_to_posting(
                job_dict=job_dict,
                source_key=source_key,
                posted_by=posted_by,
            )
            if posting is None:
                summary["skipped"] += 1
            else:
                postings_to_create.append(posting)
        except Exception as exc:
            logger.error(f"Error converting job dict: {exc}", exc_info=True)
            summary["errors"] += 1

    # Bulk-create all new postings in one transaction
    if postings_to_create:
        try:
            with transaction.atomic():
                # Generate slugs manually since bulk_create doesn't call save()
                for posting in postings_to_create:
                    if not posting.slug:
                        from django.utils.text import slugify
                        import re
                        
                        base_slug = slugify(f"{posting.job_title}-{posting.company_name}")
                        posting.slug = base_slug
                        n = 0
                        # Ensure unique slug
                        while JobPosting.objects.filter(slug=posting.slug).exists():
                            n += 1
                            # Remove any existing numeric suffix
                            clean_slug = re.sub(r'-\d+$', '', base_slug)
                            # Add new numeric suffix
                            posting.slug = f"{clean_slug}-{n}"
                
                created = JobPosting.objects.bulk_create(
                    postings_to_create,
                    ignore_conflicts=True,
                )
                summary["published"] = len(created)
        except Exception as exc:
            logger.error(f"Bulk create failed: {exc}", exc_info=True)
            summary["errors"] += len(postings_to_create)

    return summary


def publish_multiple_scraped_jobs(scraped_jobs, posted_by: User) -> dict:
    """Publish a queryset or list of ScrapedJob records. Returns aggregated summary."""
    total = {"published": 0, "skipped": 0, "errors": 0}
    for sj in scraped_jobs:
        result = publish_scraped_job(sj, posted_by)
        for k in total:
            total[k] += result[k]
    return total
