"""
Job scraper manager that supports multiple job posting websites
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def get_bossjob_scraper():
    """Lazy import to avoid circular dependencies"""
    from .scraper_utils import BossJobScraper
    return BossJobScraper


class JobScraperManager:
    """Manages multiple job scrapers and aggregates results"""
    
    def __init__(self):
        self.scrapers = {}
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """Initialize all available scrapers"""
        # Initialize BossJob.ph scraper
        try:
            BossJobScraper = get_bossjob_scraper()
            self.scrapers['BOSSJOB'] = BossJobScraper()
            logger.info("BossJob.ph scraper initialized")
        except Exception as e:
            logger.error(f"Failed to initialize BossJob scraper: {str(e)}")
        
        # TODO: Initialize other scrapers
        # try:
        #     self.scrapers['JOBSTREET'] = JobStreetScraper()
        # except Exception as e:
        #     logger.warning(f"JobStreet scraper not available: {str(e)}")
        
        # try:
        #     self.scrapers['LINKEDIN'] = LinkedInScraper()
        # except Exception as e:
        #     logger.warning(f"LinkedIn scraper not available: {str(e)}")
    
    def search_jobs(self, keyword: str, location: str, sources: Optional[List[str]] = None, use_cache: bool = True) -> Dict:
        """Search jobs across multiple sources
        
        Args:
            keyword: Job keyword or title
            location: Location to search in
            sources: List of source names to search (e.g., ['BOSSJOB', 'JOBSTREET'])
                     If None, searches all available sources
            use_cache: Whether to use cached results
            
        Returns:
            Dict with aggregated results from all sources
        """
        if sources is None:
            sources = list(self.scrapers.keys())
        
        # Filter to only available scrapers
        available_sources = [s for s in sources if s.upper() in self.scrapers]
        
        if not available_sources:
            logger.warning(f"No available scrapers for sources: {sources}")
            return {
                'success': False,
                'jobs': [],
                'total_found': 0,
                'keyword': keyword,
                'location': location,
                'message': 'No available scrapers found',
                'results_by_source': {}
            }
        
        all_jobs = []
        results_by_source = {}
        
        logger.info(f"Searching jobs for '{keyword}' in '{location}' across {len(available_sources)} source(s): {available_sources}")
        
        # Search each source
        for source_name in available_sources:
            try:
                scraper = self.scrapers[source_name]
                logger.info(f"Searching {source_name} for '{keyword}' in '{location}'...")
                
                result = scraper.search_jobs(keyword, location, use_cache=use_cache)
                
                if result and result.get('success'):
                    jobs = result.get('jobs', [])
                    # Add source information to each job
                    for job in jobs:
                        job['source'] = source_name
                        job['source_display'] = self._get_source_display_name(source_name)
                    
                    all_jobs.extend(jobs)
                    results_by_source[source_name] = {
                        'success': True,
                        'jobs_found': len(jobs),
                        'jobs': jobs,
                        'message': result.get('message', '')
                    }
                    logger.info(f"{source_name}: Found {len(jobs)} jobs")
                else:
                    results_by_source[source_name] = {
                        'success': False,
                        'jobs_found': 0,
                        'jobs': [],
                        'message': result.get('message', 'Search failed') if result else 'No response from scraper',
                        'error': result.get('error', 'Unknown error') if result else 'No response'
                    }
                    logger.warning(f"{source_name}: Search failed - {results_by_source[source_name].get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error searching {source_name}: {str(e)}", exc_info=True)
                results_by_source[source_name] = {
                    'success': False,
                    'jobs_found': 0,
                    'jobs': [],
                    'message': f'Error: {str(e)}',
                    'error': str(e)
                }
        
        # Remove duplicates based on title + company + location
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        return {
            'success': len(unique_jobs) > 0,
            'jobs': unique_jobs,
            'total_found': len(unique_jobs),
            'keyword': keyword,
            'location': location,
            'message': f"Found {len(unique_jobs)} unique job(s) from {len([s for s in results_by_source.values() if s['success']])} source(s)",
            'results_by_source': results_by_source,
            'sources_searched': available_sources
        }
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs across different sources"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create signature from title, company, and location
            signature = f"{job.get('title', '').lower().strip()}|{job.get('company', '').lower().strip()}|{job.get('location', '').lower().strip()}"
            
            if signature not in seen and len(signature) > 3:  # Ensure signature is meaningful
                seen.add(signature)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _get_source_display_name(self, source: str) -> str:
        """Get display name for source"""
        display_names = {
            'BOSSJOB': 'BossJob.ph',
            'JOBSTREET': 'JobStreet',
            'LINKEDIN': 'LinkedIn',
            'INDEED': 'Indeed',
            'GLASSDOOR': 'Glassdoor'
        }
        return display_names.get(source.upper(), source)
    
    def get_available_sources(self) -> List[str]:
        """Get list of available scraper sources"""
        return list(self.scrapers.keys())

