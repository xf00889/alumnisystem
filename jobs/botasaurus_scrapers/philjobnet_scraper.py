"""
PhilJobNet (DOLE) scraper using botasaurus.
PhilJobNet is the official Philippine government job portal run by DOLE.
Current public job listing route: https://philjobnet.gov.ph/job-vacancies/
"""
import logging
import re
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import (
    build_job_dict,
    is_meaningful_description,
    make_empty_result,
    make_success_result,
    normalize_description,
)

logger = logging.getLogger(__name__)

SOURCE = "PHILJOBNET"
BASE_URL = "https://philjobnet.gov.ph"


def _fetch_job_details(req: Request, detail_url: str, fallback_location: str) -> dict:
    """Fetch structured details from a PhilJobNet job detail page."""
    try:
        detail_resp = req.get(detail_url, timeout=12)
        detail_resp.raise_for_status()
    except Exception:
        return {}

    detail_soup = soupify(detail_resp)
    title = ""
    title_el = detail_soup.select_one("h1.jobtitle")
    if title_el:
        title = " ".join(title_el.get_text(" ", strip=True).split())

    company = ""
    company_el = detail_soup.select_one("span.companytitle")
    if company_el:
        company = " ".join(company_el.get_text(" ", strip=True).split())

    salary = ""
    salary_el = detail_soup.select_one("h3.salary span, h3.salary")
    if salary_el:
        salary = " ".join(salary_el.get_text(" ", strip=True).split())

    location = fallback_location
    labels = detail_soup.select("h3.jobdesctitle")
    values = detail_soup.select("div.jobdescription")
    for label_el, value_el in zip(labels, values):
        label = " ".join(label_el.get_text(" ", strip=True).split()).lower()
        value = " ".join(value_el.get_text(" ", strip=True).split())
        if "work location" in label and value:
            location = value
            break

    # Keep only primary description sections.
    description_parts = []
    for label_el, value_el in zip(labels, values):
        label = " ".join(label_el.get_text(" ", strip=True).split()).lower()
        value = " ".join(value_el.get_text(" ", strip=True).split())
        if not value:
            continue
        if "job description" in label:
            description_parts.append(value)
        elif "qualifications" in label or "requirements" in label:
            description_parts.append(f"Qualifications/Requirements: {value}")

    description = normalize_description("\n\n".join(description_parts))
    if not is_meaningful_description(description):
        description = ""

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "description": description,
    }


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_philjobnet(req: Request, data: dict):
    """Fetch and parse PhilJobNet job search results."""
    keyword = data["keyword"]
    location = data["location"]  # currently not directly supported by public filter
    url = f"{BASE_URL}/job-vacancies/?s={quote_plus(keyword)}"

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[PhilJobNet] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    links = soup.select("a[href*='/job-vacancies/job/']")
    for a in links[:20]:
        href = a.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = BASE_URL + href

        details = _fetch_job_details(req, href, fallback_location=location)

        # Fallback from search card only if detail parsing misses title.
        raw = " ".join(a.get_text(" ", strip=True).split())
        if not raw:
            continue
        fallback_title = raw
        # Remove everything after salary/company block if present.
        fallback_title = re.split(r"\s+salary\s+", fallback_title, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        fallback_title = fallback_title[:140].strip()

        title = details.get("title") or fallback_title
        company = details.get("company") or ""
        loc = details.get("location") or location
        salary = details.get("salary") or ""
        description = details.get("description") or ""

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location=loc,
            description=description,
            salary=salary,
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_philjobnet(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_philjobnet({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[PhilJobNet] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
