"""
OnlineJobs.ph scraper using botasaurus.
OnlineJobs.ph focuses on remote/online work for Filipino workers.
URL: https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword={keyword}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "ONLINEJOBS"
BASE_URL = "https://www.onlinejobs.ph"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_onlinejobs(req: Request, data: dict):
    """Fetch and parse OnlineJobs.ph search results."""
    keyword = data["keyword"]
    location = data["location"]

    url = (
        f"{BASE_URL}/jobseekers/jobsearch"
        f"?jobkeyword={quote_plus(keyword)}"
        "&jobregion=0"  # all regions
    )

    try:
        response = req.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"[OnlineJobs] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(response)
    jobs = []

    # OnlineJobs.ph job cards
    cards = soup.select("div.job-post-item, div[class*='job-post'], article.job-post")
    if not cards:
        cards = soup.select("div.row.job-listing, div.job-listing")

    for card in cards[:20]:
        title_el = card.select_one("h2 a, h3 a, .job-title a, a.job-title")
        company_el = card.select_one(".company-name, .employer-name, span.company")
        salary_el = card.select_one(".salary, .pay-rate, span[class*='salary']")
        job_type_el = card.select_one(".job-type, .employment-type, span[class*='type']")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
        job_type = job_type_el.get_text(strip=True) if job_type_el else "Remote"
        href = title_el.get("href", "") if title_el else ""
        if href and not href.startswith("http"):
            href = BASE_URL + href

        if not title:
            continue

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location="Remote / Philippines",
            salary=salary,
            job_type=job_type,
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_onlinejobs(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_onlinejobs({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[OnlineJobs] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
