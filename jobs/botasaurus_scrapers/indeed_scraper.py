"""
Indeed Philippines scraper using botasaurus.
URL pattern: https://ph.indeed.com/jobs?q={keyword}&l={location}
"""
import html
import json
import logging
import re
from typing import Dict
from urllib.parse import quote_plus

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from .base import (
    build_job_dict,
    is_meaningful_description,
    make_empty_result,
    make_success_result,
)

logger = logging.getLogger(__name__)

SOURCE = "INDEED"
DETAIL_FETCH_LIMIT = 8


def _normalize_description(text: str) -> str:
    """Strip HTML and keep readable line breaks for downstream cleaning."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"</(p|div|li|h1|h2|h3|h4|h5|h6|ul|ol)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _find_description_in_json(data) -> str:
    """Recursively find a suitable description field in JSON-LD objects."""
    if isinstance(data, dict):
        direct = data.get("description")
        if isinstance(direct, str):
            cleaned = _normalize_description(direct)
            if len(cleaned) >= 80:
                return cleaned
        for value in data.values():
            found = _find_description_in_json(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_description_in_json(item)
            if found:
                return found
    return ""


def _extract_json_ld_description(soup) -> str:
    """Try extracting description from JSON-LD blocks."""
    for script in soup.select("script[type='application/ld+json']"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        found = _find_description_in_json(payload)
        if found:
            return found
    return ""


def _fetch_indeed_job_description(req: Request, url: str) -> str:
    """Fetch a single Indeed job page and extract full description."""
    if not url:
        return ""
    try:
        response = req.get(url, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        logger.debug(f"[Indeed] Could not fetch detail page {url}: {exc}")
        return ""

    soup = soupify(response)

    selectors = [
        "#jobDescriptionText",
        "div[data-testid='jobsearch-JobComponent-description']",
        "div.jobsearch-jobDescriptionText",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        text = _normalize_description(node.get_text("\n", strip=True))
        if is_meaningful_description(text):
            return text

    json_ld_text = _extract_json_ld_description(soup)
    return json_ld_text if is_meaningful_description(json_ld_text) else ""


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
        snippet_el = card.select_one("div.job-snippet, div.job-snippet-container")
        link_el = card.select_one("a[id^='job_'], a.jcs-JobTitle, h2.jobTitle a")

        title = (
            title_el.get("title") or title_el.get_text(strip=True)
            if title_el else ""
        )
        company = company_el.get_text(strip=True) if company_el else ""
        loc = location_el.get_text(strip=True) if location_el else ""
        salary = salary_el.get_text(strip=True) if salary_el else ""
        description = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://ph.indeed.com" + href

        if not title:
            continue

        if href and len(jobs) < DETAIL_FETCH_LIMIT:
            full_description = _fetch_indeed_job_description(req, href)
            if full_description:
                description = full_description
        if not is_meaningful_description(description):
            description = ""

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
