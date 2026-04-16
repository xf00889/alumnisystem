"""
BossJob.ph scraper using botasaurus.
BossJob is a heavily JS-rendered site, so we use the @browser decorator
with google_get to bypass Cloudflare and extract job data.
URL: https://bossjob.ph/en-us/jobs-hiring/{keyword}-jobs-in-{location}
"""
import logging
from typing import Dict

from botasaurus.browser import browser, Driver
from botasaurus.soupify import soupify

from .base import build_job_dict, make_empty_result, make_success_result

logger = logging.getLogger(__name__)

SOURCE = "BOSSJOB"
BASE_URL = "https://bossjob.ph"


@browser(
    output=None,
    raise_exception=False,
    close_on_crash=True,
    max_retry=2,
    headless=True,
    block_images_and_css=True,
    wait_for_complete_page_load=False,
)
def _fetch_bossjob(driver: Driver, data: dict):
    """Fetch and parse BossJob.ph search results using a headless browser."""
    keyword = data["keyword"]
    location = data["location"]

    kw_slug = keyword.lower().replace(" ", "%20")
    loc_slug = location.lower().replace(" ", "-")
    url = f"{BASE_URL}/en-us/jobs-hiring/{kw_slug}-jobs-in-{loc_slug}"

    try:
        driver.google_get(url)
        # Wait briefly for JS to render job cards
        driver.short_random_sleep()
    except Exception as exc:
        logger.warning(f"[BossJob] Navigation failed: {exc}")
        return make_empty_result(keyword, location, SOURCE, str(exc))

    soup = soupify(driver)
    jobs = []

    # BossJob uses Next.js CSS modules — try multiple selector patterns
    selectors = [
        "div[class*='listItem']",
        "div[class*='jobCard']",
        "div[data-sentry-component='JobCardPc']",
        ".job-card",
        "article",
    ]
    cards = []
    for sel in selectors:
        cards = soup.select(sel)
        if cards:
            break

    for card in cards[:20]:
        # Title
        title_el = (
            card.select_one("h3[class*='jobHireTopTitle'] span")
            or card.select_one("h3[class*='jobHireTopTitle']")
            or card.select_one("h2")
            or card.select_one("h3")
        )
        # Company
        company_el = (
            card.select_one("[class*='jobHireRecruiterName']")
            or card.select_one("[class*='listCompany'] p")
            or card.select_one("p")
        )
        # Location — filter out non-location tags
        location_els = card.select("[class*='jobCardLocationItem'], [class*='listTag'] span")
        loc_text = ""
        for el in location_els:
            t = el.get_text(strip=True).lower()
            if any(kw in t for kw in ["manila", "cebu", "davao", "makati", "taguig",
                                       "pasig", "quezon", "bgc", "ortigas", "remote",
                                       "on-site", "hybrid", "ncr", "philippines"]):
                loc_text = el.get_text(strip=True)
                break

        # Salary
        salary_el = card.select_one("[class*='salaryText'], [class*='salary']")
        # URL
        link_el = card.select_one("a[href*='/job/'], a[href*='/jobs/'], a")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = BASE_URL + href

        if not title or len(title) < 3:
            continue

        jobs.append(build_job_dict(
            title=title,
            company=company,
            location=loc_text or location,
            salary=salary,
            url=href,
            source=SOURCE,
        ))

    return make_success_result(keyword, location, SOURCE, jobs)


def scrape_bossjob(keyword: str, location: str) -> Dict:
    """Public entry point. Returns a result dict."""
    try:
        result = _fetch_bossjob({"keyword": keyword, "location": location})
        if isinstance(result, list):
            result = result[0] if result else {}
        return result or make_empty_result(keyword, location, SOURCE, "No result returned")
    except Exception as exc:
        logger.error(f"[BossJob] Unexpected error: {exc}", exc_info=True)
        return make_empty_result(keyword, location, SOURCE, str(exc))
