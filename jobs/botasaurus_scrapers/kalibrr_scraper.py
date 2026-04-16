"""
Kalibrr Philippines scraper using botasaurus.
Kalibrr exposes a public JSON API for job search.
API: https://www.kalibrr.com/api/job_board/search?keyword={keyword}&location={location}
"""
import logging
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "KALIBRR"
BASE_URL = "https://www.kalibrr.com"


@request(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=3,
)
def _fetch_kalibrr(req: Request, data: dict):
    """Fetch and parse Kalibrr job search via their JSON API."""
    keyword = data["keyword"]
    location = data["location"]

    api_url = (
        f"{BASE_URL}/api/job_board/search"
        f"?keyword={quote_plus(keyword)}"
        f"&location={quote_plus(location)}"
        "&limit=20&offset=0"
    )

    try:
        response = req.get(api_url, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.warning(f"[Kalibrr] Request failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    jobs = []
    job_list = payload.get("jobs") or payload.get("data") or []

    for item in job_list[:20]:
        title = item.get("title") or item.get("name") or ""
        company = (
            (item.get("company") or {}).get("name")
            or item.get("company_name")
            or ""
        )
        loc = item.get("location") or item.get("city") or ""
        salary = item.get("salary") or item.get("salary_range") or ""
        job_type = item.get("employment_type") or item.get("job_type") or ""
        slug = item.get("slug") or item.get("id") or ""
        url = f"{BASE_URL}/jobs/{slug}" if slug else ""

        if not title:
            continue

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location=loc,
            salary=str(salary) if salary else "",
            job_type=job_type,
            url=url,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_kalibrr(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_kalibrr({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[Kalibrr] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
