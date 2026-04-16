"""
Indeed Philippines scraper using botasaurus.
URL pattern: https://ph.indeed.com/jobs?q={keyword}&l={location}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "INDEED"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_indeed(req: Request, data: dict):
    """Fetch and parse Indeed PH search results."""
    keyword = data["keyword"]
    location = data["location"]

    url = (
        f"https://ph.indeed.com/jobs"
        f"?q={quote_plus(keyword)}&l={quote_plus(location)}"
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[Indeed] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # Indeed job cards use data-jk attribute
    cards = soup.select("div.job_seen_beacon, div[data-jk]")
    if not cards:
        cards = soup.select("div.tapItem")

    for card in cards[:20]:
        title_el = (
            card.select_one("h2.jobTitle span[title]")
            or card.select_one("h2.jobTitle")
            or card.select_one("a.jcs-JobTitle")
        )
        company_el = card.select_one("span.companyName, [data-testid='company-name']")
        location_el = card.select_one("div.companyLocation, [data-testid='text-location']")
        salary_el = card.select_one("div.salary-snippet-container, div.metadata.salary-snippet-container")
        link_el = card.select_one("a[id^='job_'], a.jcs-JobTitle, h2.jobTitle a")

        title = (
            title_el.get("title") or title_el.get_text(strip=True)
            if title_el else ""
        )
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://ph.indeed.com" + href

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


def scrape_indeed(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_indeed({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[Indeed] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
