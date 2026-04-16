"""
LinkedIn Jobs scraper using botasaurus.
Uses the public jobs search endpoint (no login required for listings).
URL: https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "LINKEDIN"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_linkedin(req: Request, data: dict):
    """Fetch and parse LinkedIn public job search results."""
    keyword = data["keyword"]
    location = data["location"]

    url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={quote_plus(keyword)}"
        f"&location={quote_plus(location)}"
        "&f_TPR=r86400"  # last 24 hours filter
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[LinkedIn] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # LinkedIn public job cards
    cards = soup.select("div.base-card, li.jobs-search__results-list > div")
    if not cards:
        cards = soup.select("li.result-card")

    for card in cards[:20]:
        title_el = card.select_one(
            "h3.base-search-card__title, h3.result-card__title"
        )
        company_el = card.select_one(
            "h4.base-search-card__subtitle, h4.result-card__subtitle"
        )
        location_el = card.select_one(
            "span.job-search-card__location, span.result-card__location"
        )
        link_el = card.select_one("a.base-card__full-link, a.result-card__full-card-link")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        href = link_el.get("href", "") if link_el else ""

        if not title:
            continue

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location=loc,
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_linkedin(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_linkedin({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[LinkedIn] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
