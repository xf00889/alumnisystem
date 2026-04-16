"""
Mynimo Philippines scraper using botasaurus.
Mynimo focuses on Visayas and Mindanao job listings.
URL: https://www.mynimo.com/search?q={keyword}&location={location}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "MYNIMO"
BASE_URL = "https://www.mynimo.com"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_mynimo(req: Request, data: dict):
    """Fetch and parse Mynimo search results."""
    keyword = data["keyword"]
    location = data["location"]

    url = (
        f"{BASE_URL}/search"
        f"?q={quote_plus(keyword)}"
        f"&location={quote_plus(location)}"
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[Mynimo] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # Mynimo job listing cards
    cards = soup.select("div.job-listing, article.job, div[class*='job-item']")
    if not cards:
        cards = soup.select("div.listing-item, li.listing")

    for card in cards[:20]:
        title_el = card.select_one("h2 a, h3 a, .job-title a, a.title")
        company_el = card.select_one(".company, .employer, span.company-name")
        location_el = card.select_one(".location, .job-location, span.location")
        salary_el = card.select_one(".salary, span.salary")
        job_type_el = card.select_one(".job-type, .employment-type")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
        job_type = job_type_el.get_text(strip=True) if job_type_el else ""
        href = title_el.get("href", "") if title_el else ""
        if href and not href.startswith("http"):
            href = BASE_URL + href

        if not title:
            continue

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location=loc,
            salary=salary,
            job_type=job_type,
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_mynimo(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_mynimo({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[Mynimo] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
