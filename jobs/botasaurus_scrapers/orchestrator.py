"""
Orchestrator for running all Philippine job site scrapers.

Usage:
    from jobs.botasaurus_scrapers.orchestrator import scrape_all_sites, SCRAPERS

    results = scrape_all_sites("software engineer", "Manila")
    # results is a list of result dicts, one per site

Each result dict has the shape:
    {
        "success": bool,
        "jobs": [...],
        "total_found": int,
        "keyword": str,
        "location": str,
        "source": str,   # e.g. "JOBSTREET"
        "message": str,
        "error": str,    # only on failure
    }
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from .bossjob_scraper import scrape_bossjob
from .jobstreet_scraper import scrape_jobstreet
from .indeed_scraper import scrape_indeed
from .kalibrr_scraper import scrape_kalibrr
from .linkedin_scraper import scrape_linkedin
from .philjobnet_scraper import scrape_philjobnet
from .onlinejobs_scraper import scrape_onlinejobs
from .jora_scraper import scrape_jora
from .mynimo_scraper import scrape_mynimo
from .workabroad_scraper import scrape_workabroad

logger = logging.getLogger(__name__)

# Registry: source key → (display name, scraper function)
SCRAPERS: Dict[str, tuple] = {
    "JOBSTREET":  ("JobStreet Philippines",  scrape_jobstreet),
    "INDEED":     ("Indeed Philippines",     scrape_indeed),
    "LINKEDIN":   ("LinkedIn",               scrape_linkedin),
    "KALIBRR":    ("Kalibrr",               scrape_kalibrr),
    "BOSSJOB":    ("BossJob.ph",             scrape_bossjob),
    "PHILJOBNET": ("PhilJobNet (DOLE)",      scrape_philjobnet),
    "ONLINEJOBS": ("OnlineJobs.ph",          scrape_onlinejobs),
    "JORA":       ("Jora Philippines",       scrape_jora),
    "MYNIMO":     ("Mynimo",                 scrape_mynimo),
    "WORKABROAD": ("WorkAbroad.ph",          scrape_workabroad),
}


def scrape_site(source_key: str, keyword: str, location: str) -> Dict:
    """Run a single scraper by source key and return its result dict."""
    if source_key not in SCRAPERS:
        return {
            "success": False,
            "jobs": [],
            "total_found": 0,
            "keyword": keyword,
            "location": location,
            "source": source_key,
            "error": f"Unknown source: {source_key}",
            "message": f"Unknown source: {source_key}",
        }
    display_name, fn = SCRAPERS[source_key]
    logger.info(f"[Orchestrator] Scraping {display_name} for '{keyword}' in '{location}'")
    try:
        result = fn(keyword, location)
        return result
    except Exception as exc:
        logger.error(f"[Orchestrator] {display_name} failed: {exc}", exc_info=True)
        return {
            "success": False,
            "jobs": [],
            "total_found": 0,
            "keyword": keyword,
            "location": location,
            "source": source_key,
            "error": str(exc),
            "message": str(exc),
        }


def scrape_all_sites(
    keyword: str,
    location: str,
    sources: Optional[List[str]] = None,
    max_workers: int = 4,
) -> List[Dict]:
    """
    Run scrapers for all (or selected) sites in parallel.

    Args:
        keyword:     Job search keyword.
        location:    Location string (city, region, or "Philippines").
        sources:     Optional list of source keys to limit scraping.
                     Defaults to all 10 sites.
        max_workers: Thread pool size. Keep ≤ 4 to be respectful.

    Returns:
        List of result dicts, one per site attempted.
    """
    target_sources = sources or list(SCRAPERS.keys())
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_source = {
            pool.submit(scrape_site, src, keyword, location): src
            for src in target_sources
        }
        for future in as_completed(future_to_source):
            src = future_to_source[future]
            try:
                result = future.result()
            except Exception as exc:
                logger.error(f"[Orchestrator] Future for {src} raised: {exc}", exc_info=True)
                result = {
                    "success": False,
                    "jobs": [],
                    "total_found": 0,
                    "keyword": keyword,
                    "location": location,
                    "source": src,
                    "error": str(exc),
                    "message": str(exc),
                }
            results.append(result)

    # Sort by source key for deterministic ordering
    results.sort(key=lambda r: r.get("source", ""))
    return results


def aggregate_jobs(results: List[Dict]) -> List[Dict]:
    """
    Flatten all jobs from multiple scraper results into a single deduplicated list.

    Deduplication is based on (normalised title, normalised company).
    """
    seen = set()
    all_jobs = []
    for result in results:
        for job in result.get("jobs", []):
            key = (
                job.get("title", "").lower().strip(),
                job.get("company", "").lower().strip(),
            )
            if key not in seen:
                seen.add(key)
                all_jobs.append(job)
    return all_jobs
