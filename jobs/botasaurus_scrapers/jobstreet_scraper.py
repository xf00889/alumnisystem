"""
JobStreet Philippines scraper using botasaurus.
URL pattern: https://www.jobstreet.com.ph/jobs/{keyword}-jobs-in-{location}
"""
import logging
from typing import Dict

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "JOBSTREET"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_jobstreet(req: Request, data: dict):
    """Fetch and parse JobStreet PH search results."""
    keyword = data["keyword"]
    location = data["location"]

    kw_slug = keyword.lower().replace(" ", "-")
    loc_slug = location.lower().replace(" ", "-")
    url = f"https://www.jobstreet.com.ph/jobs/{kw_slug}-jobs-in-{loc_slug}"

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[JobStreet] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # JobStreet renders job cards with data-automation attributes
    cards = soup.select("article[data-automation='normalJob'], article[data-automation='featuredJob']")
    if not cards:
        # Fallback: any article with a job-related class
        cards = soup.select("article")

    for card in cards[:20]:
        title_el = card.select_one("[data-automation='jobTitle']")
        company_el = card.select_one("[data-automation='jobCompany']")
        location_el = card.select_one("[data-automation='jobLocation']")
        salary_el = card.select_one("[data-automation='jobSalary']")
        link_el = card.select_one("a[data-automation='jobTitle']") or card.select_one("a")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.jobstreet.com.ph" + href

        if not title:
            continue

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location=loc,
            salary=salary,
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_jobstreet(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_jobstreet({"keyword": keyword, "location": location})
        # botasaurus returns a list when given a single dict; unwrap it
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[JobStreet] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
