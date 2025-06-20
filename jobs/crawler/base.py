"""
Base crawler class that defines the interface for all job crawlers.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """Base class for all job site crawlers."""
    
    def __init__(self, delay: float = 1.0, max_jobs: int = 100):
        """
        Initialize the crawler.
        
        Args:
            delay: Time in seconds to wait between requests
            max_jobs: Maximum number of jobs to fetch
        """
        self.delay = delay
        self.max_jobs = max_jobs
        self.source_name = self.get_source_name()
        logger.info(f"Initialized {self.source_name} crawler")
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of the job source (e.g., 'indeed', 'linkedin')."""
        pass
    
    @abstractmethod
    def search_jobs(self, query: str, location: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for jobs with the given query and location.
        
        Args:
            query: Job search query (e.g., 'python developer')
            location: Location to search in (e.g., 'San Francisco, CA')
            **kwargs: Additional search parameters
        
        Returns:
            List of job dictionaries with at least the following fields:
            - title: Job title
            - company: Company name
            - location: Job location
            - url: URL to job posting
            - description: Job description
            - source_id: Unique identifier from the source
        """
        pass
    
    @abstractmethod
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a job from its URL.
        
        Args:
            job_url: URL to the job posting
        
        Returns:
            Dictionary with detailed job information
        """
        pass
    
    def standardize_job_data(self, job_data):
        """
        Standardize job data to match the JobPosting model.
        
        Args:
            job_data: Dictionary containing job data from the crawler
            
        Returns:
            Dictionary with standardized job data
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Generate a hash signature for deduplication
            import hashlib
            import json
            
            # Use relevant fields to create a hash
            hash_fields = {
                'title': job_data.get('title', ''),
                'company': job_data.get('company', ''),
                'url': job_data.get('url', ''),
                'location': job_data.get('location', '')
            }
            
            hash_string = json.dumps(hash_fields, sort_keys=True).encode('utf-8')
            hash_signature = hashlib.md5(hash_string).hexdigest()
            
            # Process and standardize job data
            standardized_data = {
                'job_title': job_data.get('title', 'Unknown Title'),
                'company_name': job_data.get('company', 'Unknown Company'),
                'location': job_data.get('location', ''),
                'job_description': job_data.get('description', ''),
                'application_link': job_data.get('url', ''),
                'source': job_data.get('source', self.get_source_name()),
                'hash_signature': hash_signature,
                'external_id': job_data.get('source_id', ''),  # Map source_id to external_id
                'job_type': self._normalize_job_type(job_data.get('job_type', '')),
                'is_active': True
            }
            
            # Process salary range with better formatting
            salary = job_data.get('salary_range', '')
            if salary:
                # Normalize the salary representation
                import re
                
                # Clean up the salary text
                salary = re.sub(r'\s+', ' ', salary).strip()
                
                # Extract numeric values and format consistently
                salary_match = re.search(r'(\$[\d,]+\.?\d*|\d[\d,]*\.?\d*\s*[kK]|\d[\d,.]*\s*-\s*\d[\d,.]*\s*[kK]?)', salary)
                if salary_match:
                    salary_value = salary_match.group(1)
                    if '$' not in salary_value and 'PHP' not in salary and 'php' not in salary.lower():
                        # Add currency symbol if missing
                        salary = f"PHP {salary}"
                
                standardized_data['salary_range'] = salary
            
            # Add requirements if present
            if 'requirements' in job_data and job_data['requirements']:
                standardized_data['requirements'] = job_data['requirements']
            
            # Add responsibilities if present
            if 'responsibilities' in job_data and job_data['responsibilities']:
                standardized_data['responsibilities'] = job_data['responsibilities']
                
            # Add skills if present
            if 'skills' in job_data and job_data['skills']:
                standardized_data['skills_required'] = job_data['skills']
                
            # Add search metadata
            if 'search_query' in job_data:
                standardized_data['search_query'] = job_data['search_query']
            if 'search_location' in job_data:
                standardized_data['search_location'] = job_data['search_location']
            if 'category' in job_data:
                standardized_data['category'] = job_data['category']
                
            # Add posted date if present, otherwise default to current time
            standardized_data['posted_date'] = job_data.get('posted_date', timezone.now())
            
            return standardized_data
            
        except Exception as e:
            logger.error(f"Error standardizing job data: {str(e)}")
            # Return minimal data to avoid failures
            return {
                'job_title': job_data.get('title', 'Unknown Title'),
                'company_name': job_data.get('company', 'Unknown Company'),
                'application_link': job_data.get('url', ''),
                'source': self.get_source_name(),
                'is_active': True
            }
    
    def _normalize_job_type(self, raw_job_type: str) -> str:
        """
        Normalize job types to match JobPosting.JOB_TYPE_CHOICES.
        
        Args:
            raw_job_type: Raw job type string from the job listing
            
        Returns:
            Normalized job type that matches the model's job type choices
        """
        job_type = raw_job_type.lower()
        
        if 'full' in job_type or 'ft' in job_type:
            return 'FULLTIME'
        elif 'part' in job_type or 'pt' in job_type:
            return 'PARTTIME'
        elif 'contract' in job_type or 'freelance' in job_type:
            return 'CONTRACT'
        elif 'intern' in job_type:
            return 'INTERNSHIP'
        elif 'temp' in job_type or 'temporary' in job_type:
            return 'TEMPORARY'
        else:
            return 'FULLTIME'  # Default to full-time
    
    def sleep(self):
        """Sleep between requests to avoid rate limiting."""
        time.sleep(self.delay) 