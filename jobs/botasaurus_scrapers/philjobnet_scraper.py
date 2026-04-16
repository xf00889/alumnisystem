"""
PhilJobNet (DOLE) scraper using botasaurus.
PhilJobNet is the official Philippine government job portal run by DOLE.
URL: https://www.philjobnet.gov.ph/index.php?option=com_jobsearch&view=jobsearch
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "PHILJOBNET"
BASE_URL = "https://www.philjobnet.gov.ph"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_philjobnet(req: Request, data: dict):
    """Fetch and parse PhilJobNet job search results."""
    keyword = data["keyword"]
    location = data["location"]

    # PhilJobNet search form
    url = (
        f"{BASE_URL}/index.php?option=com_jobsearch&view=jobsearch"
        f"&keyword={quote_plus(keyword)}"
        f"&location={quote_plus(location)}"
        "&task=search"
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[PhilJobNet] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # PhilJobNet uses a table-based layout for job listings
    rows = soup.select("table.job-list tr, div.job-item, div.job-listing-item")
    if not rows:
        # Try generic table rows
        rows = soup.select("tr.job-row, tr[class*='job']")

    for row in rows[:20]:
        title_el = row.select_one("td.job-title a, .job-title a, h3 a, h4 a")
        company_el = row.select_one("td.company-name, .company-name, .employer")
        location_el = row.select_one("td.location, .location, .job-location")
        salary_el = row.select_one("td.salary, .salary")

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
