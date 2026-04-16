"""
Jora Philippines scraper using botasaurus.
Jora aggregates jobs from multiple sources.
URL: https://ph.jora.com/j?q={keyword}&l={location}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "JORA"
BASE_URL = "https://ph.jora.com"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_jora(req: Request, data: dict):
    """Fetch and parse Jora PH search results."""
    keyword = data["keyword"]
    location = data["location"]

    url = (
        f"{BASE_URL}/j"
        f"?q={quote_plus(keyword)}"
        f"&l={quote_plus(location)}"
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[Jora] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # Jora job cards
    cards = soup.select("article.job-card, div.job-card, li.job-card")
    if not cards:
        cards = soup.select("[class*='job-card'], [class*='jobCard']")

    for card in cards[:20]:
        title_el = card.select_one("a.job-link, h2 a, h3 a, .job-title")
        company_el = card.select_one(".company, .employer, span[class*='company']")
        location_el = card.select_one(".location, .job-location, span[class*='location']")
        salary_el = card.select_one(".salary, span[class*='salary']")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
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
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_jora(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_jora({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[Jora] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
