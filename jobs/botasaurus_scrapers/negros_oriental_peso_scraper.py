"""Public PEIS vacancy-category monitoring for Negros Oriental Provincial PESO.

PEIS publishes *aggregated counts by office and occupation*, not individual
employer advertisements. Results are review-only leads, NEVER JobPosting rows.
No login, Facebook automation, personal data, or unverified job details.
"""
import logging
import re
import time
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from .base import make_empty_result

logger = logging.getLogger(__name__)
SOURCE = "PESO_NEGROS_ORIENTAL"
OFFICE = "NEGROS ORIENTAL PROVINCIAL PESO"
HOMEPAGE = "https://peis.philjobnet.gov.ph/"
HOST = "peis.philjobnet.gov.ph"
MAX_CATEGORIES = 12
MAX_PAGE_BYTES = 1_000_000
# The public homepage contains a short top-vacancies sample, not the full registry.
USER_AGENT = "NORSU-Alumni-PublicVacancyMonitor/1.0 (+https://www.norsualumni.com/)"


def _approved_url(url):
    """Restrict fetches to public PEIS homepage and vacancy detail URLs."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != HOST or parsed.username:
        return False
    if parsed.path.lower() in ("", "/", "/default.aspx", "/index.aspx") and not parsed.query:
        return True
    if parsed.path.lower() != "/details.aspx":
        return False
    params = parse_qs(parsed.query)
    ids = params.get("id", [])
    return len(ids) == 1 and ids[0].isdigit() and params.get("t", [""])[0].lower() == "vacancies"


def _get_html(session, url):
    if not _approved_url(url):
        raise ValueError("Unapproved PEIS address")
    # Prevent a redirect to an unrelated host by rejecting it before following.
    response = session.get(url, timeout=(3, 7), allow_redirects=False, headers={"User-Agent": USER_AGENT})
    if response.status_code in (301, 302, 303, 307, 308):
        location = urljoin(url, response.headers.get("Location", ""))
        if not _approved_url(location):
            raise ValueError("PEIS redirected outside approved public pages")
        response = session.get(location, timeout=(3, 7), allow_redirects=False, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    if len(response.content) > MAX_PAGE_BYTES:
        raise ValueError("PEIS response exceeds size limit")
    return response.text


def public_vacancy_categories(html):
    """Collect only PEIS links explicitly marked t=vacancies (not skills)."""
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    categories = []
    for link in soup.select('a[href]'):
        href = urljoin(HOMEPAGE, link.get("href", ""))
        if not _approved_url(href) or urlsplit(href).path.lower() != "/details.aspx":
            continue
        title = " ".join(link.get_text(" ", strip=True).split())
        if not title or not re.search(r"[a-zA-Z]", title):
            continue
        # Link caption is the occupation; vacancy volume beside it is national.
        title = re.sub(r"\s*\([\d,]+\)\s*$", "", title).strip()[:160]
        if href in seen:
            continue
        seen.add(href)
        categories.append((title, href))
        if len(categories) >= MAX_CATEGORIES:
            break
    return categories


def provincial_vacancy_count(html):
    """Extract the exact Negros Oriental Provincial PESO row; never sum others."""
    soup = BeautifulSoup(html, "html.parser")
    for item in soup.select("li, tr"):
        text = " ".join(item.get_text(" ", strip=True).split())
        match = re.fullmatch(r"NEGROS ORIENTAL PROVINCIAL PESO\s*\(([\d,]+)\)", text, re.I)
        if match:
            return int(match.group(1).replace(",", ""))
    # Some PEIS versions do not use list elements; safe exact-text fallback.
    text = " ".join(soup.get_text(" ", strip=True).split())
    match = re.search(r"(?<![A-Z])NEGROS ORIENTAL PROVINCIAL PESO\s*\(([\d,]+)\)", text, re.I)
    return int(match.group(1).replace(",", "")) if match else 0


def scrape_negros_oriental_peso(keyword, location):
    """Return review-only occupation leads, not employer job postings.

    A count is tied to a registering PESO office, NOT necessarily a vacancy
    physically located in Negros Oriental. Never convert to a live job listing.
    """
    try:
        with requests.Session() as session:
            homepage = _get_html(session, HOMEPAGE)
            categories = public_vacancy_categories(homepage)
            leads = []
            errors = 0
            checked = 0
            deadline = time.monotonic() + 44
            for idx, (title, detail_url) in enumerate(categories):
                if keyword and keyword.lower().strip() not in title.lower():
                    continue
                if time.monotonic() >= deadline:
                    break
                if checked:
                    time.sleep(0.4)  # Small delay between public page requests.
                checked += 1
                try:
                    count = provincial_vacancy_count(_get_html(session, detail_url))
                except (requests.RequestException, ValueError) as exc:
                    errors += 1
                    logger.warning("[PESO Negros Oriental] Cannot read vacancy category: %s", type(exc).__name__)
                    continue
                if count <= 0:
                    continue
                leads.append({
                    "title": title,
                    "office": OFFICE,
                    "vacancy_count": count,
                    "source_url": detail_url,
                    "status": "office_aggregate_unverified",
                })
    except (requests.RequestException, ValueError) as exc:
        logger.warning("[PESO Negros Oriental] Public PEIS retrieval failed: %s", type(exc).__name__)
        result = make_empty_result(keyword, location, SOURCE, "The public PEIS vacancy overview is currently unavailable.")
        result.update({"vacancy_leads": [], "lead_count": 0})
        return result

    return {
        "success": bool(categories) and (checked == 0 or errors < checked),
        "source": SOURCE,
        "keyword": keyword,
        "location": OFFICE,
        "jobs": [],
        "total_found": 0,
        "vacancy_leads": leads,
        "lead_count": len(leads),
        "aggregate_vacancy_count": sum(item["vacancy_count"] for item in leads),
        "source_page": HOMEPAGE,
        "source_scope": "public_top_occupations_sample",
        "publishable": False,
        "message": (
            f"Found {len(leads)} public occupation lead(s) under {OFFICE}. "
            "Figures are aggregated by registration office, not verified individual job ads "
            "or proof of employment location. Verify with PESO before posting."
        ),
    }
