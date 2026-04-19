"""
PhilJobNet (DOLE) scraper using botasaurus.
PhilJobNet is the official Philippine government job portal run by DOLE.
Current public job listing route: https://philjobnet.gov.ph/job-vacancies/
"""
import logging
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


def _fetch_job_description(req: Request, detail_url: str) -> str:
    """Fetch description from a PhilJobNet job detail page."""
    try:
        detail_resp = req.get(detail_url, timeout=12)
        detail_resp.raise_for_status()
    except Exception:
        return ""

    detail_soup = soupify(detail_resp)
    # Current site uses a structured "jobdescription" block.
    node = (
        detail_soup.select_one("div.jobdescription")
        or detail_soup.select_one("div.row.mb-3.jobdescription")
        or detail_soup.select_one("div.icon-box")
    )
    if not node:
        return ""

    text = normalize_description(node.get_text("\n", strip=True))
    return text if is_meaningful_description(text) else ""


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

        # Card link text is a compact summary block.
        raw = " ".join(a.get_text(" ", strip=True).split())
        if not raw:
            continue

        # Typical summary starts with title then salary/company/location etc.
        # Use conservative extraction to avoid malformed fields.
        title = raw.split(" Salary", 1)[0].strip() if " Salary" in raw else raw[:120].strip()
        company = ""
        loc = location
        salary = ""

        description = _fetch_job_description(req, href)

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
