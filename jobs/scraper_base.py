"""
Base scraper interface for multiple job posting websites
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseJobScraper(ABC):
    """Base class for job scrapers"""
    
    def __init__(self):
        self.base_url = None
        self.source_name = None
    
    @abstractmethod
    def search_jobs(self, keyword: str, location: str, use_cache: bool = True) -> Dict:
        """Search for jobs on the job site
        
        Args:
            keyword: Job keyword or title to search for
            location: Location to search in
            use_cache: Whether to use cached results
            
        Returns:
            Dict with keys:
                - success: bool
                - jobs: List[Dict] - List of job dictionaries
                - total_found: int
                - keyword: str
                - location: str
                - message: str
                - debug_info: Dict (optional)
        """
        pass
    
    @abstractmethod
    def _extract_jobs(self, content, keyword: str = '') -> List[Dict]:
        """Extract job listings from page content
        
        Args:
            content: Page content (HTML, JSON, etc.)
            keyword: Search keyword for relevance filtering
            
        Returns:
            List of job dictionaries with keys:
                - title: str
                - company: str
                - location: str
                - description: str
                - salary: str
                - url: str
        """
        pass
    
    def normalize_job_data(self, job: Dict) -> Dict:
        """Normalize job data to standard format"""
        return {
            'title': job.get('title', '') or 'Job Title Not Available',
            'company': job.get('company', '') or 'Company Not Specified',
            'location': job.get('location', '') or 'Location Not Specified',
            'description': job.get('description', '') or 'No description available',
            'salary': job.get('salary', '') or 'Salary not disclosed',
            'url': job.get('url', '') or '#',
            'source': self.source_name or 'Unknown'
        }

