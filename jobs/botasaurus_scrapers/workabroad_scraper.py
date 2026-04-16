"""
WorkAbroad.ph scraper using botasaurus.
WorkAbroad.ph focuses on overseas Filipino worker (OFW) job listings.
URL: https://www.workabroad.ph/search-jobs.php?q={keyword}&country={location}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "WORKABROAD"
BASE_URL = "https://www.workabroad.ph"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_workabroad(req: Request, data: dict):
    """Fetch and parse WorkAbroad.ph search results."""
    keyword = data["keyword"]
    location = data["location"]

    url = (
        f"{BASE_URL}/search-jobs.php"
        f"?q={quote_plus(keyword)}"
        f"&country={quote_plus(location)}"
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[WorkAbroad] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # WorkAbroad job listing rows/cards
    cards = soup.select("div.job-listing, div.job-item, tr.job-row")
    if not cards:
        cards = soup.select("div[class*='job'], article[class*='job']")

    for card in cards[:20]:
        title_el = card.select_one("h2 a, h3 a, .job-title a, td.job-title a")
        company_el = card.select_one(".company, .agency, .employer, td.company")
        location_el = card.select_one(".country, .location, td.country, td.location")
        salary_el = card.select_one(".salary, td.salary")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else location
        salary = salary_el.get_text(strip=True) if salary_el else ""
        href = title_el.get("href", "") if title_el else ""
        if href and not href.startswith("http"):
            href = BASE_URL + "/" + href.lstrip("/")

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


def scrape_workabroad(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_workabroad({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[WorkAbroad] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
