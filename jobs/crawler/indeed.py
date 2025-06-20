"""
Indeed job crawler implementation.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote
from django.utils import timezone

from .base import BaseCrawler

logger = logging.getLogger(__name__)

class IndeedCrawler(BaseCrawler):
    """Crawler for Indeed.com job listings."""
    
    BASE_URL = "https://www.indeed.com"
    SEARCH_URL = BASE_URL + "/jobs"
    
    def get_source_name(self) -> str:
        """Return the name of the job source."""
        return "indeed"
    
    def search_jobs(self, query: str, location: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed with the given query and location.
        
        Args:
            query: Job search query (e.g., 'python developer')
            location: Location to search in (e.g., 'San Francisco, CA')
            **kwargs: Additional search parameters
                - job_type: Filter by job type (e.g., 'fulltime', 'parttime')
                - radius: Search radius in miles (e.g., 10)
                - sort: Sort by relevance or date ('relevance', 'date')
                - days: Filter by days since posting (e.g., 14 for two weeks)
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        page = 0
        params = {
            'q': query,
            'l': location,
        }
        
        # Add additional parameters if provided
        if 'job_type' in kwargs:
            params['jt'] = kwargs['job_type']
        if 'radius' in kwargs:
            params['radius'] = kwargs['radius']
        if 'sort' in kwargs:
            params['sort'] = kwargs['sort']
        if 'days' in kwargs:
            params['fromage'] = str(kwargs['days'])
            
        logger.info(f"Searching Indeed for '{query}' in '{location}'")
        
        while len(jobs) < self.max_jobs:
            if page > 0:
                params['start'] = page * 10
                
            try:
                logger.debug(f"Fetching Indeed search page {page+1}")
                response = requests.get(self.SEARCH_URL, params=params, 
                                       headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.job_seen_beacon')
                
                if not job_cards:
                    logger.debug("No more job cards found")
                    break
                
                for card in job_cards:
                    try:
                        # Extract job ID
                        job_id_tag = card.get('data-jk') or card.get('id')
                        if not job_id_tag:
                            continue
                            
                        job_id = job_id_tag.replace('job_', '')
                        
                        # Extract job URL
                        job_link = card.select_one('h2.jobTitle a')
                        if not job_link:
                            continue
                            
                        job_url = urljoin(self.BASE_URL, job_link.get('href'))
                        
                        # Extract basic job info
                        title = job_link.get_text(strip=True)
                        company_tag = card.select_one('span.companyName')
                        company = company_tag.get_text(strip=True) if company_tag else 'Unknown'
                        
                        location_tag = card.select_one('div.companyLocation')
                        location = location_tag.get_text(strip=True) if location_tag else ''
                        
                        # Extract job type if available
                        job_type_tag = card.select_one('div.metadata')
                        job_type = job_type_tag.get_text(strip=True) if job_type_tag else ''
                        
                        # Extract salary if available
                        salary_tag = card.select_one('div.salary-snippet')
                        salary_range = salary_tag.get_text(strip=True) if salary_tag else ''
                        
                        # Extract posting date
                        date_tag = card.select_one('span.date')
                        posted_date = self._parse_date(date_tag.get_text(strip=True)) if date_tag else timezone.now()
                        
                        # Extract snippet
                        snippet_tag = card.select_one('div.job-snippet')
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': job_url,
                            'source_id': job_id,
                            'description': snippet,
                            'job_type': job_type,
                            'salary_range': salary_range,
                            'posted_date': posted_date,
                        })
                        
                        if len(jobs) >= self.max_jobs:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error parsing job card: {str(e)}")
                
                # Check if there's a next page
                next_page = soup.select_one('a[data-testid="pagination-page-next"]')
                if not next_page:
                    break
                    
                page += 1
                self.sleep()
                
            except Exception as e:
                logger.error(f"Error fetching search results: {str(e)}")
                break
                
        logger.info(f"Found {len(jobs)} jobs on Indeed")
        return jobs[:self.max_jobs]
    
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a job from its URL.
        
        Args:
            job_url: URL to the Indeed job posting
            
        Returns:
            Dictionary with detailed job information
        """
        logger.debug(f"Fetching job details from {job_url}")
        
        try:
            response = requests.get(job_url, 
                                  headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job ID from URL
            job_id_match = re.search(r'jk=([^&]+)', job_url)
            job_id = job_id_match.group(1) if job_id_match else None
            
            # Extract job title
            title_tag = soup.select_one('h1.jobsearch-JobInfoHeader-title')
            title = title_tag.get_text(strip=True) if title_tag else 'Unknown Title'
            
            # Extract company name
            company_tag = soup.select_one('div.jobsearch-CompanyInfoContainer a.jobsearch-InlineCompanyRating-companyName')
            company = company_tag.get_text(strip=True) if company_tag else 'Unknown Company'
            
            # Extract location
            location_tag = soup.select_one('div.jobsearch-JobInfoHeader-subtitle div')
            location = location_tag.get_text(strip=True) if location_tag else ''
            
            # Extract job description
            description_tag = soup.select_one('div#jobDescriptionText')
            description = str(description_tag) if description_tag else ''
            
            # Extract salary
            salary_tag = soup.select_one('span.jobsearch-JobMetadataHeader-item')
            salary_range = salary_tag.get_text(strip=True) if salary_tag else ''
            
            # Try to extract requirements and responsibilities from description
            requirements = ''
            responsibilities = ''
            skills = ''
            
            if description_tag:
                # Look for requirements section
                req_headers = description_tag.find_all(['h2', 'h3', 'h4', 'strong'], string=re.compile(r'requirements|qualifications', re.I))
                if req_headers:
                    for header in req_headers:
                        # Get the text content following this header until the next header
                        req_text = []
                        for sibling in header.next_siblings:
                            if sibling.name in ['h2', 'h3', 'h4', 'strong']:
                                break
                            if sibling.string:
                                req_text.append(sibling.string.strip())
                        requirements = ' '.join(req_text)
                        break
                
                # Look for responsibilities section
                resp_headers = description_tag.find_all(['h2', 'h3', 'h4', 'strong'], 
                                                      string=re.compile(r'responsibilities|duties', re.I))
                if resp_headers:
                    for header in resp_headers:
                        # Get the text content following this header until the next header
                        resp_text = []
                        for sibling in header.next_siblings:
                            if sibling.name in ['h2', 'h3', 'h4', 'strong']:
                                break
                            if sibling.string:
                                resp_text.append(sibling.string.strip())
                        responsibilities = ' '.join(resp_text)
                        break
                
                # Try to extract skills using common patterns
                skill_patterns = [
                    r'experience with ([\w\s,\.]+)',
                    r'knowledge of ([\w\s,\.]+)',
                    r'proficient in ([\w\s,\.]+)',
                    r'skills: ([\w\s,\.]+)',
                    r'technical skills: ([\w\s,\.]+)'
                ]
                
                desc_text = description_tag.get_text()
                found_skills = []
                
                for pattern in skill_patterns:
                    matches = re.finditer(pattern, desc_text, re.IGNORECASE)
                    for match in matches:
                        found_skills.append(match.group(1).strip())
                
                skills = ', '.join(found_skills)
            
            # Extract job type
            job_type = ''
            job_type_tags = soup.select('div.jobsearch-JobMetadataHeader-item')
            for tag in job_type_tags:
                text = tag.get_text().lower()
                if any(t in text for t in ['full-time', 'part-time', 'contract', 'temporary', 'internship']):
                    job_type = tag.get_text(strip=True)
                    break
            
            # Extract posting date
            date_tag = soup.select_one('span.jobsearch-JobMetadataFooter-item')
            posted_date = timezone.now()
            if date_tag:
                date_text = date_tag.get_text(strip=True)
                if 'posted' in date_text.lower():
                    posted_date = self._parse_date(date_text)
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'requirements': requirements,
                'responsibilities': responsibilities,
                'skills': skills,
                'job_type': job_type,
                'salary_range': salary_range,
                'url': job_url,
                'source_id': job_id,
                'posted_date': posted_date,
            }
            
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return {}
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date strings like '30+ days ago', 'Today', etc."""
        date_text = date_text.lower()
        now = timezone.now()
        
        if 'today' in date_text:
            return now
        
        if 'just posted' in date_text:
            return now
            
        if 'yesterday' in date_text:
            return now - timedelta(days=1)
            
        if 'ago' in date_text:
            # Handle "X days ago"
            days_match = re.search(r'(\d+)\s*day', date_text)
            if days_match:
                days = int(days_match.group(1))
                return now - timedelta(days=days)
                
            # Handle "X hours ago"
            hours_match = re.search(r'(\d+)\s*hour', date_text)
            if hours_match:
                hours = int(hours_match.group(1))
                return now - timedelta(hours=hours)
        
        # Handle "30+ days ago" as 30 days
        if '30+' in date_text:
            return now - timedelta(days=30)
            
        # Default to current time if we can't parse
        return now