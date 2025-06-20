"""
BossJobs job crawler implementation.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote, urlparse
from django.utils import timezone

from .base import BaseCrawler

logger = logging.getLogger(__name__)

class BossJobsCrawler(BaseCrawler):
    """Crawler for BossJobs job listings."""
    
    BASE_URL = "https://www.bossjob.ph"  # Updated to the Philippine domain
    SEARCH_URL = BASE_URL + "/jobs"
    
    # Define career categories for diverse job searches
    CAREER_CATEGORIES = {
        'technology': [
            'technology', 'software', 'developer', 'programmer', 'it', 
            'engineer', 'tech', 'data', 'computer'
        ],
        'finance': [
            'finance', 'accounting', 'accountant', 'banking', 'financial', 
            'auditor', 'tax', 'budget', 'bookkeeper'
        ],
        'healthcare': [
            'healthcare', 'medical', 'nurse', 'doctor', 'physician',
            'healthcare', 'hospital', 'clinic', 'patient', 'therapy'
        ],
        'education': [
            'education', 'teaching', 'teacher', 'instructor', 'professor',
            'school', 'university', 'tutor', 'academic'
        ],
        'sales_marketing': [
            'sales', 'marketing', 'advertising', 'market', 'brand', 
            'digital-marketing', 'social-media', 'promotion'
        ],
        'hospitality': [
            'hospitality', 'hotel', 'restaurant', 'tourism', 'chef',
            'customer-service', 'food', 'beverage', 'travel'
        ],
        'manufacturing': [
            'manufacturing', 'production', 'factory', 'warehouse', 
            'logistics', 'supply-chain', 'quality-control'
        ],
        'administrative': [
            'administrative', 'office', 'clerical', 'secretary', 
            'receptionist', 'assistant', 'administration'
        ],
        'construction': [
            'construction', 'building', 'architect', 'civil-engineer', 
            'electrician', 'plumber', 'carpenter'
        ],
        'creative': [
            'creative', 'design', 'graphic', 'content', 'writer',
            'photography', 'media', 'art', 'artist', 'creative'
        ]
    }
    
    def __init__(self, delay: float = 1.0, max_jobs: int = 100):
        """
        Initialize the crawler.
        
        Args:
            delay: Time in seconds to wait between requests
            max_jobs: Maximum number of jobs to fetch
        """
        super().__init__(delay, max_jobs)
        self.jobs_seen = set()  # Track seen job URLs to avoid duplicates across searches
    
    def get_source_name(self) -> str:
        """Return the name of the job source."""
        return "bossjobs"
    
    def search_jobs(self, query: str, location: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for jobs on BossJobs with the given query and location.
        
        Args:
            query: Job search query (e.g., 'python developer')
            location: Location to search in (e.g., 'Philippines')
            **kwargs: Additional search parameters
                - job_type: Filter by job type (e.g., 'fulltime', 'parttime')
                - page: Page number to start from
                - limit: Maximum number of jobs to fetch per page
                - category: The job category context (e.g., 'finance', 'healthcare')
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Extract category context if provided
        category = kwargs.get('category')
        
        # Try different URL formats and domains
        domains_to_try = [
            "https://www.bossjob.ph",
            "https://www.bossjob.com"
        ]
        
        # Try different search URL patterns
        search_patterns = [
            "/jobs/search?q={query}&l={location}&page={page}",
            "/jobs?q={query}&l={location}&page={page}",
            "/jobs/search/{query}?page={page}",
            "/jobs/categories/{query}?page={page}",  # Added category search pattern
            "/jobs?page={page}",  # Try all jobs with pagination
        ]
        
        max_pages = min(kwargs.get('max_pages', 10), 20)  # Increased from 5,10 to 10,20
        start_page = kwargs.get('page', 1)
        
        logger.info(f"Searching BossJobs for '{query}' in '{location}' with max_pages={max_pages}, max_jobs={self.max_jobs}, category={category}")
        
        # Try each domain and pattern until we find job listings
        for domain in domains_to_try:
            if len(jobs) >= self.max_jobs:
                break
                
            for pattern in search_patterns:
                if len(jobs) >= self.max_jobs:
                    break
                    
                for page in range(start_page, start_page + max_pages):
                    if len(jobs) >= self.max_jobs:
                        break
                        
                    # Prepare the search URL
                    encoded_query = quote(query)
                    encoded_location = quote(location) if location else ""
                    
                    # Format the search URL based on the pattern
                    try:
                        if "{location}" in pattern:
                            if encoded_location:
                                search_url = domain + pattern.format(query=encoded_query, location=encoded_location, page=page)
                            else:
                                # Skip patterns requiring location if location is empty
                                continue
                        else:
                            search_url = domain + pattern.format(query=encoded_query, page=page)
                        
                        if 'job_type' in kwargs and "?" in search_url:
                            search_url += f"&jt={kwargs['job_type']}"
                            
                        logger.debug(f"Trying search URL: {search_url}")
                        
                        found_jobs = self._scrape_job_page(search_url, location)
                        if found_jobs:
                            # Filter out jobs we've already seen
                            new_jobs = []
                            for job in found_jobs:
                                if job['url'] not in self.jobs_seen:
                                    # Add category context if available
                                    if category:
                                        job['category'] = category
                                    self.jobs_seen.add(job['url'])
                                    new_jobs.append(job)
                                    
                            if new_jobs:
                                logger.info(f"Found {len(new_jobs)} new jobs using {domain} with pattern '{pattern}' on page {page}")
                                jobs.extend(new_jobs)
                            else:
                                logger.debug(f"No new jobs found on page {page}, skipping to next pattern")
                                break  # No new jobs, try next pattern
                                
                            # If we found jobs with this pattern, stick with it for remaining pages
                            break_outer_loop = False
                            for page_num in range(page + 1, start_page + max_pages):
                                if len(jobs) >= self.max_jobs:
                                    break_outer_loop = True
                                    break
                                    
                                try:
                                    if "{location}" in pattern:
                                        if encoded_location:
                                            next_page_url = domain + pattern.format(query=encoded_query, location=encoded_location, page=page_num)
                                        else:
                                            continue
                                    else:
                                        next_page_url = domain + pattern.format(query=encoded_query, page=page_num)
                                        
                                    self.sleep()
                                    more_jobs = self._scrape_job_page(next_page_url, location)
                                    
                                    # Filter out jobs we've already seen
                                    new_jobs = []
                                    for job in more_jobs:
                                        if job['url'] not in self.jobs_seen:
                                            if category:
                                                job['category'] = category
                                            self.jobs_seen.add(job['url'])
                                            new_jobs.append(job)
                                            
                                    if new_jobs:
                                        logger.info(f"Found {len(new_jobs)} more new jobs on page {page_num}")
                                        jobs.extend(new_jobs)
                                    else:
                                        logger.debug(f"No more new jobs found on page {page_num}")
                                        break_outer_loop = True
                                        break
                                except Exception as e:
                                    logger.warning(f"Error with paginated URL: {str(e)}")
                                    continue
                            
                            if break_outer_loop:
                                break
                    except Exception as e:
                        logger.warning(f"Error with URL pattern {pattern}: {str(e)}")
                        continue
        
        # If category is provided, try using category-specific search approaches
        if category and len(jobs) < self.max_jobs and category in self.CAREER_CATEGORIES:
            category_terms = self.CAREER_CATEGORIES[category]
            logger.info(f"Using category-specific search terms for '{category}': {category_terms}")
            
            for domain in domains_to_try:
                if len(jobs) >= self.max_jobs:
                    break
                    
                for category_term in category_terms:
                    if len(jobs) >= self.max_jobs:
                        break
                        
                    # Try category-specific URLs
                    category_urls = [
                        f"{domain}/jobs/categories/{category_term}",
                        f"{domain}/jobs/tag/{category_term}",
                        f"{domain}/jobs/{category_term}"
                    ]
                    
                    for category_url in category_urls:
                        if len(jobs) >= self.max_jobs:
                            break
                            
                        try:
                            logger.info(f"Trying category URL: {category_url}")
                            self.sleep()
                            category_jobs = self._scrape_job_page(category_url, location)
                            
                            # Only add jobs we haven't seen before
                            new_category_jobs = []
                            for job in category_jobs:
                                if job['url'] not in self.jobs_seen:
                                    job['category'] = category
                                    self.jobs_seen.add(job['url'])
                                    new_category_jobs.append(job)
                                    
                            if new_category_jobs:
                                logger.info(f"Found {len(new_category_jobs)} new jobs from category {category_term}")
                                jobs.extend(new_category_jobs)
                                
                                # Try pagination for this category if it worked
                                for page in range(2, 6):  # Try pages 2-5
                                    if len(jobs) >= self.max_jobs:
                                        break
                                        
                                    paginated_url = f"{category_url}?page={page}"
                                    logger.debug(f"Trying category page: {paginated_url}")
                                    self.sleep()
                                    page_jobs = self._scrape_job_page(paginated_url, location)
                                    
                                    # Filter for new jobs
                                    new_page_jobs = []
                                    for job in page_jobs:
                                        if job['url'] not in self.jobs_seen:
                                            job['category'] = category
                                            self.jobs_seen.add(job['url'])
                                            new_page_jobs.append(job)
                                                
                                    if new_page_jobs:
                                        logger.info(f"Found {len(new_page_jobs)} more new jobs on category page {page}")
                                        jobs.extend(new_page_jobs)
                                    else:
                                        break  # No more new jobs on this page
                                        
                        except Exception as e:
                            logger.warning(f"Error with category URL {category_url}: {str(e)}")
        
        # If we still haven't found enough jobs, try more specific approaches
        if len(jobs) < self.max_jobs / 2:
            logger.info(f"Only found {len(jobs)} jobs, trying alternative search approaches...")
            
            # Try more specific career category pages based on broad career fields
            categories = [
                'technology', 'software', 'developer', 'engineer', 'programming',
                'design', 'marketing', 'sales', 'finance', 'accounting',
                'customer-service', 'data-science', 'healthcare', 'education',
                'hospitality', 'tourism', 'administrative', 'clerical', 'construction',
                'manufacturing', 'logistics', 'legal', 'media', 'creative', 'hr',
                'management', 'retail', 'food-and-beverage', 'transport',
                query.lower().replace(' ', '-'),  # Try using the query as a category
            ]
            
            # If we have a category context, prioritize those category terms
            if category and category in self.CAREER_CATEGORIES:
                # Add category-specific terms at the beginning
                categories = self.CAREER_CATEGORIES[category] + [c for c in categories if c not in self.CAREER_CATEGORIES[category]]
            
            for domain in domains_to_try:
                if len(jobs) >= self.max_jobs:
                    break
                    
                for category_term in categories:
                    if len(jobs) >= self.max_jobs:
                        break
                        
                    category_urls = [
                        f"{domain}/jobs/categories/{category_term}",
                        f"{domain}/jobs/tag/{category_term}",
                        f"{domain}/jobs/{category_term}"
                    ]
                    
                    for category_url in category_urls:
                        if len(jobs) >= self.max_jobs:
                            break
                            
                        try:
                            logger.info(f"Trying category URL: {category_url}")
                            self.sleep()
                            category_jobs = self._scrape_job_page(category_url, location)
                            
                            # Only add jobs we haven't seen before
                            new_category_jobs = []
                            for job in category_jobs:
                                if job['url'] not in self.jobs_seen:
                                    # Only add jobs with actual titles if possible
                                    if job.get('title') != 'Unknown Title':
                                        if category:
                                            job['category'] = category
                                        self.jobs_seen.add(job['url'])
                                        new_category_jobs.append(job)
                                        
                            if new_category_jobs:
                                logger.info(f"Found {len(new_category_jobs)} new jobs from category {category_term}")
                                jobs.extend(new_category_jobs)
                                
                                # Try pagination for this category if it worked
                                for page in range(2, 6):  # Try pages 2-5
                                    if len(jobs) >= self.max_jobs:
                                        break
                                        
                                    paginated_url = f"{category_url}?page={page}"
                                    logger.debug(f"Trying category page: {paginated_url}")
                                    self.sleep()
                                    page_jobs = self._scrape_job_page(paginated_url, location)
                                    
                                    # Filter for new jobs
                                    new_page_jobs = []
                                    for job in page_jobs:
                                        if job['url'] not in self.jobs_seen:
                                            if job.get('title') != 'Unknown Title':
                                                if category:
                                                    job['category'] = category
                                                self.jobs_seen.add(job['url'])
                                                new_page_jobs.append(job)
                                                
                                    if new_page_jobs:
                                        logger.info(f"Found {len(new_page_jobs)} more new jobs on category page {page}")
                                        jobs.extend(new_page_jobs)
                                    else:
                                        break  # No more new jobs on this page
                                        
                        except Exception as e:
                            logger.warning(f"Error with category URL {category_url}: {str(e)}")
        
        # Add browse-all approach as a final fallback
        if len(jobs) < self.max_jobs / 2:
            logger.info("Trying browse-all approach for more job diversity")
            
            browse_urls = [
                f"{domain}/jobs" for domain in domains_to_try
            ]
            
            for browse_url in browse_urls:
                if len(jobs) >= self.max_jobs:
                    break
                    
                try:
                    logger.info(f"Browsing all jobs: {browse_url}")
                    self.sleep()
                    all_jobs = self._scrape_job_page(browse_url, location)
                    
                    # Only add jobs we haven't seen before
                    new_all_jobs = []
                    for job in all_jobs:
                        if job['url'] not in self.jobs_seen:
                            if category:
                                job['category'] = category
                            self.jobs_seen.add(job['url'])
                            new_all_jobs.append(job)
                            
                    if new_all_jobs:
                        logger.info(f"Found {len(new_all_jobs)} new jobs from browsing all")
                        jobs.extend(new_all_jobs)
                        
                        # Try pagination for browse all
                        for page in range(2, 11):  # Try pages 2-10
                            if len(jobs) >= self.max_jobs:
                                break
                                
                            paginated_url = f"{browse_url}?page={page}"
                            logger.debug(f"Trying browse all page: {paginated_url}")
                            self.sleep()
                            page_jobs = self._scrape_job_page(paginated_url, location)
                            
                            # Filter for new jobs
                            new_page_jobs = []
                            for job in page_jobs:
                                if job['url'] not in self.jobs_seen:
                                    if category:
                                        job['category'] = category
                                    self.jobs_seen.add(job['url'])
                                    new_page_jobs.append(job)
                                    
                            if new_page_jobs:
                                logger.info(f"Found {len(new_page_jobs)} more new jobs on browse page {page}")
                                jobs.extend(new_page_jobs)
                            else:
                                break  # No more new jobs on this page
                                
                except Exception as e:
                    logger.warning(f"Error with browse URL {browse_url}: {str(e)}")
        
        # At this point, we should have deduplicated jobs based on URL
        # Let's also deduplicate based on title+company to remove more duplicates
        title_company_jobs = {}
        for job in jobs:
            key = f"{job.get('title', '')}-{job.get('company', '')}"
            if key not in title_company_jobs:
                title_company_jobs[key] = job
        
        # Now deduplicate by URL (this should be redundant but we'll do it anyway)
        url_deduplicated_jobs = {}
        for job in title_company_jobs.values():
            if job['url'] not in url_deduplicated_jobs:
                url_deduplicated_jobs[job['url']] = job
            elif job.get('title') != 'Unknown Title' and url_deduplicated_jobs[job['url']].get('title') == 'Unknown Title':
                # Replace "Unknown Title" with better titles
                url_deduplicated_jobs[job['url']] = job
        
        filtered_jobs = list(url_deduplicated_jobs.values())
        raw_count = len(jobs)
        filtered_count = len(filtered_jobs)
        final_count = min(filtered_count, self.max_jobs)
        
        logger.info(f"BossJobs job search complete. Raw jobs: {raw_count}, Filtered jobs: {filtered_count}, Final returned: {final_count}")
        if filtered_count > self.max_jobs:
            logger.warning(f"Found {filtered_count} jobs but only returning {self.max_jobs} due to max_jobs limit")
        
        # For BossJobs, we need to improve title/company extraction
        # The issue: what's extracted as the "company" in search results is actually the job title we want to display
        for job in filtered_jobs[:self.max_jobs]:
            # Check if title is same as company (indicating the extraction issue we're trying to fix)
            if job.get('title', '').strip() == job.get('company', '').strip() and job.get('url'):
                logger.warning(f"Title equals company '{job.get('title')}', fetching detailed info for company name")
                try:
                    # Fetch detailed job info to get the actual company name
                    self.sleep()  # Be nice to the server
                    detailed_job = self.get_job_details(job['url'])
                    
                    if detailed_job and detailed_job.get('company'):
                        # The company from detailed page is the actual company
                        actual_company = detailed_job['company']
                        
                        # What we had as title/company in search results is actually the job title we want
                        # This often contains useful information like salary and experience requirements
                        search_result_title = job['title']
                        
                        logger.debug(f"BEFORE FIX - Job URL: {job['url']}")
                        logger.debug(f"BEFORE FIX - Title: '{job.get('title', '')}'")
                        logger.debug(f"BEFORE FIX - Company: '{job.get('company', '')}'")
                        logger.debug(f"DETAILED - Company: '{actual_company}'")
                        logger.debug(f"DETAILED - Title: '{detailed_job.get('title', '')}'")
                        
                        # For BossJobs, the search result title is actually more informative than the detailed title
                        # It contains salary, experience requirements, and often the job role in English
                        # Example: "SEO Specialist＄3-5K[Monthly]Remote · 1-3 Yrs Exp · Bachelor · Full-time"
                        
                        # For non-Chinese speakers, the original search result title is most useful
                        # It contains the job role in English and additional details
                        final_title = search_result_title
                        
                        logger.info(f"Using search result title: '{final_title}'")
                        logger.info(f"Using company from detailed page: '{actual_company}'")
                        
                        # Update the job data
                        job['title'] = final_title
                        job['company'] = actual_company
                        
                        logger.debug(f"AFTER FIX - Title: '{job.get('title', '')}'")
                        logger.debug(f"AFTER FIX - Company: '{job.get('company', '')}'")
                except Exception as e:
                    logger.error(f"Error fixing title/company: {str(e)}")
                    # If we can't get company info, at least make them different
                    # to avoid duplicate display issues
                    job['company'] = job.get('company', 'Unknown') + " (Employer)"
        
        # Return up to max_jobs jobs
        return filtered_jobs[:self.max_jobs]
    
    def _scrape_job_page(self, url: str, location: str) -> List[Dict[str, Any]]:
        """Scrape a single page of job results."""
        jobs = []
        
        try:
            logger.debug(f"Fetching job page: {url}")
            response = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                    "Referer": self.BASE_URL
                },
                timeout=15
            )
            response.raise_for_status()
            
            if not response.text.strip():
                logger.error("Empty HTML response received")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # First try to find job cards using common selectors
            job_card_selectors = [
                'div.job-card', 'div.job-listing', 'div[data-job-id]',
                'div.job-post-card', 'div.job-search-card', 'div.job-item',
                'div[class*="job-card"]', 'div[class*="job-listing"]',
                'div.card', 'article.job', 'div.search-result-card'
            ]
            
            # Try each selector until we find job cards
            job_cards = []
            for selector in job_card_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    logger.debug(f"Found {len(job_cards)} job cards with selector: {selector}")
                    break
            
            # If we found job cards, process them
            if job_cards:
                for card in job_cards:
                    try:
                        # Find job link
                        job_link = None
                        link_selectors = [
                            'a[href*="/job/"]', 'a[href*="/jobs/"]', 
                            'a.job-title-link', 'a.job-card-title',
                            'a[class*="job-title"]', 'a[class*="title"]',
                            'h2 a', 'h3 a', 'h4 a'
                        ]
                        
                        for selector in link_selectors:
                            job_link = card.select_one(selector)
                            if job_link and job_link.get('href'):
                                break
                        
                        if not job_link or not job_link.get('href'):
                            continue
                            
                        job_url = urljoin(self.BASE_URL, job_link.get('href'))
                        
                        # Skip company pages and validate job URL
                        if '/company/' in job_url or not self._is_valid_job_url(job_url):
                            continue
                            
                        # Extract job ID
                        job_id = self._extract_job_id(job_url)
                        if not job_id:
                            continue

                        # Debug the card's raw HTML to help with selector debugging
                        logger.debug(f"Processing job card HTML: {str(card)[:200]}...")
                                
                        # Start with more aggressive extraction to avoid company/title confusion
                        # Extract company name first (important to do this before title extraction)
                        company_selectors = [
                            'span.company-name', 'div.company-name', 'a.company-name',
                            '[class*="company-name"]', '[class*="employer-name"]',
                            'span.company', 'div.company', '.employer',
                            '[itemprop="hiringOrganization"]', '[data-company]'
                        ]
                        company = "Unknown Company"
                        company_elem = None
                        for selector in company_selectors:
                            company_elem = card.select_one(selector)
                            if company_elem:
                                company = company_elem.get_text(strip=True)
                                logger.debug(f"Found company name with selector '{selector}': '{company}'")
                                break
                        
                        # Now extract job title with more specific selectors
                        title_selectors = [
                            '[class*="job-title"]', '[class*="jobtitle"]', 
                            'a.job-title', 'span.job-title', 'div.job-title',
                            'h2.title', 'h3.title', 'h2.job-title', 'h3.job-title',
                            '[itemprop="title"]', '[data-job-title]'
                        ]
                        
                        title = None
                        title_elem = None
                        
                        # Try specific title selectors first
                        for selector in title_selectors:
                            title_elem = card.select_one(selector)
                            if title_elem and title_elem.get_text(strip=True):
                                potential_title = title_elem.get_text(strip=True)
                                if potential_title != company:
                                    title = potential_title
                                    logger.debug(f"Found title with selector '{selector}': '{title}'")
                                    break
                        
                        # If no title found, use the link text if it's not the same as company
                        if not title and job_link and job_link.get_text(strip=True):
                            potential_title = job_link.get_text(strip=True)
                            if potential_title != company:
                                title = potential_title
                                logger.debug(f"Using link text as title: '{title}'")
                        
                        # If still no title, look for heading elements
                        if not title:
                            for heading in ['h1', 'h2', 'h3', 'h4', 'h5']:
                                heading_elem = card.find(heading)
                                if heading_elem and heading_elem.get_text(strip=True):
                                    potential_title = heading_elem.get_text(strip=True)
                                    if potential_title != company:
                                        title = potential_title
                                        logger.debug(f"Using {heading} text as title: '{title}'")
                                        break
                        
                        # If still no title, try to extract from URL
                        if not title:
                            job_url_parts = job_url.split('/')
                            for i in range(len(job_url_parts)-1, 0, -1):
                                part = job_url_parts[i]
                                if part and part != 'job' and part != 'jobs' and not part.isdigit():
                                    potential_title = part.replace('-', ' ').title()
                                    if potential_title != company:
                                        title = potential_title
                                        logger.debug(f"Extracted title from URL: '{title}'")
                                        break
                        
                        # If still no title, try to fetch from detailed page (expensive but accurate)
                        if not title:
                            logger.info(f"No title found in card, fetching detailed job page: {job_url}")
                            try:
                                self.sleep()
                                detailed_job = self.get_job_details(job_url)
                                if detailed_job and detailed_job.get('title'):
                                    title = detailed_job['title']
                                    logger.info(f"Got title from detailed page: '{title}'")
                            except Exception as e:
                                logger.error(f"Error fetching detailed job for title: {str(e)}")
                        
                        # Last resort fallback
                        if not title:
                            title = "Unknown Title"
                            logger.warning(f"Could not extract title for job at {job_url}")
                        
                        # Extract location
                        location_selectors = [
                            '[class*="location"]', 'span.location', 'div.location',
                            'span.job-location', 'div.job-location'
                        ]
                        job_location = ""
                        for selector in location_selectors:
                            location_elem = card.select_one(selector)
                            if location_elem:
                                job_location = location_elem.get_text(strip=True)
                                break
                        
                        # If job location is empty, use the search location
                        if not job_location:
                            job_location = location
                        
                        # Extract job type
                        job_type_selectors = [
                            '[class*="job-type"]', 'span.job-type', 'div.job-type',
                            '[class*="employment"]', 'span.employment-type', 'div.employment-type'
                        ]
                        job_type = ""
                        for selector in job_type_selectors:
                            job_type_elem = card.select_one(selector)
                            if job_type_elem:
                                job_type = job_type_elem.get_text(strip=True)
                                break
                        
                        # Extract salary
                        salary_selectors = [
                            '[class*="salary"]', 'span.salary', 'div.salary',
                            'span.salary-range', 'div.salary-range'
                        ]
                        salary = ""
                        for selector in salary_selectors:
                            salary_elem = card.select_one(selector)
                            if salary_elem:
                                salary = salary_elem.get_text(strip=True)
                                break
                        
                        # Extract description snippet
                        snippet_selectors = [
                            '[class*="description"]', 'span.description', 'div.description',
                            'p.job-snippet', 'div.job-snippet', '[class*="snippet"]'
                        ]
                        snippet = ""
                        for selector in snippet_selectors:
                            snippet_elem = card.select_one(selector)
                            if snippet_elem:
                                snippet = snippet_elem.get_text(strip=True)
                                break
                        
                        # Extract date
                        date_selectors = [
                            '[class*="date"]', 'span.date', 'div.date',
                            'time', '[datetime]'
                        ]
                        posted_date = timezone.now()
                        for selector in date_selectors:
                            date_elem = card.select_one(selector)
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                                posted_date = self._parse_date(date_text)
                                break
                        
                        # Create job entry
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': job_location or location,  # Use found location or search location
                            'url': job_url,
                            'source_id': str(job_id),
                            'description': snippet,
                            'job_type': job_type,
                            'salary_range': salary,
                            'posted_date': posted_date,
                        })
                        
                        if len(jobs) >= self.max_jobs:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing job card: {str(e)}")
                
                # Return found jobs if we have any
                if jobs:
                    return jobs
            
            # If we didn't find job cards or couldn't extract jobs from them,
            # look for any links that might point to job listings
            job_links = []
            for a_tag in soup.select('a[href]'):
                href = a_tag.get('href', '')
                # Only consider links that look like job URLs
                if '/job/' in href or '/jobs/' in href:
                    if not href.endswith('/jobs/') and not href.endswith('/job/'):
                        if '/company/' not in href:  # Exclude company pages
                            job_links.append(a_tag)
            
            if job_links:
                logger.debug(f"Found {len(job_links)} potential job links")
                
                # Process these links as job listings
                for link in job_links:
                    try:
                        job_url = urljoin(self.BASE_URL, link.get('href', ''))
                        
                        # Skip company pages and other non-job URLs
                        if '/company/' in job_url:
                            continue
                            
                        # Validate that this looks like a job URL
                        if not self._is_valid_job_url(job_url):
                            continue
                            
                        # Extract job ID from URL
                        job_id = self._extract_job_id(job_url)
                        if not job_id:
                            continue
                            
                        # Try to extract job title from link
                        title = link.get_text(strip=True)
                        
                        # If link text is empty, look for a heading near the link
                        if not title:
                            # Try parent elements
                            parent = link.parent
                            if parent:
                                # Check for headings in the parent
                                header = parent.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                                if header:
                                    title = header.get_text(strip=True)
                            
                            # Try siblings
                            if not title:
                                for sibling in link.next_siblings:
                                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div'] and sibling.get_text(strip=True):
                                        title = sibling.get_text(strip=True)
                                        break
                            
                            # If all else fails, extract from URL
                            if not title:
                                # Try to extract from URL path 
                                url_path = urlparse(job_url).path
                                path_parts = url_path.strip('/').split('/')
                                if len(path_parts) > 1:
                                    # Get the last part before any ID
                                    title_part = None
                                    for part in reversed(path_parts):
                                        if not part.isdigit() and not part == 'job' and not part == 'jobs':
                                            title_part = part
                                            break
                                    
                                    if title_part:
                                        # Convert slug to title case
                                        title = title_part.replace('-', ' ').title()
                        
                        if not title:
                            title = "Job Position"
                            
                        # Try to find company name
                        company = "Unknown Company"
                        company_elem = None
                        
                        # Look in parent element for company name
                        parent = link.parent
                        if parent:
                            company_elem = parent.find(class_=lambda c: c and ('company' in c.lower()))
                            if company_elem:
                                company = company_elem.get_text(strip=True)
                        
                        # Create a job entry
                        job_entry = {
                            'title': title,
                            'company': company,
                            'location': location,  # Use the search location parameter
                            'url': job_url,
                            'source_id': str(job_id),
                            'description': "",  # Will be filled by get_job_details
                            'job_type': "",
                            'salary_range': "",
                            'posted_date': timezone.now(),
                        }
                        
                        jobs.append(job_entry)
                        if len(jobs) >= self.max_jobs:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing job link: {str(e)}")
            
            return jobs
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error scraping job page: {str(e)}")
            return []
    
    def _is_valid_job_url(self, url: str) -> bool:
        """Check if a URL is a valid job URL."""
        # Exclude company pages and ensure URL looks like a job page
        if '/company/' in url:
            return False
            
        # Check that URL contains job identifiers
        job_identifiers = ['/job/', '/jobs/view/', '/jobs/detail/']
        for identifier in job_identifiers:
            if identifier in url:
                return True
                
        # Check URL pattern for numeric ID
        url_path = urlparse(url).path
        if re.search(r'/\d+(?:/|$)', url_path):
            return True
            
        return False
    
    def _extract_job_id(self, url: str) -> Optional[str]:
        """Extract job ID from URL."""
        # Try multiple patterns to extract job ID
        patterns = [
            r'/jobs?/(?:view|detail)/(\d+)',  # /job/view/123 or /jobs/detail/123
            r'/jobs?/[^/]+/(\d+)',            # /job/title-slug/123
            r'/(\d+)(?:/|$)'                  # /123/ or /123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        # If we can't extract a numeric ID, generate one from the URL
        path = urlparse(url).path
        if path:
            # Use the path as a unique identifier
            import hashlib
            return hashlib.md5(path.encode()).hexdigest()[:8]
            
        return None
    
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a job from its URL.
        
        Args:
            job_url: URL to the BossJobs job posting
            
        Returns:
            Dictionary with detailed job information
        """
        logger.debug(f"Fetching job details from {job_url}")
        
        if not self._is_valid_job_url(job_url):
            logger.warning(f"Not a valid job URL: {job_url}")
            return {}
        
        try:
            # Extract job ID from URL
            job_id = self._extract_job_id(job_url)
            if not job_id:
                logger.error(f"Could not extract job ID from URL: {job_url}")
                return {}
                
            # Fetch the job details page
            response = requests.get(
                job_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml"
                },
                timeout=15
            )
            response.raise_for_status()
            
            # Check if we got a proper response
            if not response.text.strip():
                logger.error("Empty HTML response received")
                return {}
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple CSS selectors for different elements
            
            # Extract job title - try several approaches
            title = "Unknown Title"
            original_title = ""
            
            # Try page headings first (most reliable for detail pages)
            title_selectors = ['h1[class*="title"]', 'h1.job-title', 'h1', 'h2.job-title', '[class*="job-title"]']
            for selector in title_selectors:
                title_tag = soup.select_one(selector)
                if title_tag and title_tag.get_text(strip=True):
                    original_title = title_tag.get_text(strip=True)
                    break
                    
            # If that didn't work, try with meta tags
            if not original_title:
                meta_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'})
                if meta_title and meta_title.get('content'):
                    original_title = meta_title.get('content')
                    
            # Try document title
            if not original_title:
                title_tag = soup.find('title')
                if title_tag:
                    doc_title = title_tag.get_text(strip=True)
                    # Clean up document title
                    if ' | ' in doc_title:
                        original_title = doc_title.split(' | ')[0].strip()
                    elif ' - ' in doc_title:
                        original_title = doc_title.split(' - ')[0].strip()
                    else:
                        original_title = doc_title
            
            # Try extracting from URL if all else fails
            if not original_title:
                url_path = urlparse(job_url).path
                path_parts = [p for p in url_path.strip('/').split('/') if p and not p.isdigit() and p not in ['job', 'jobs']]
                if path_parts:
                    # Take the most specific part (usually the last meaningful segment)
                    job_slug = path_parts[-1]
                    # Convert slug to title
                    original_title = job_slug.replace('-', ' ').title()
            
            # Now process the original title to get a user-friendly version
            if original_title:
                # Check if the title contains English text
                english_parts = re.findall(r'[A-Za-z][A-Za-z\s\-]+', original_title)
                english_title = ' '.join(english_parts).strip()
                
                # Look for common job roles in the title or URL
                job_roles = [
                    'Developer', 'Engineer', 'Specialist', 'Manager', 'Analyst', 
                    'Designer', 'Representative', 'Assistant', 'Director', 
                    'Coordinator', 'Supervisor', 'Programmer', 'Architect',
                    'Administrator', 'Consultant', 'Lead', 'Expert', 'Officer'
                ]
                
                # Check if we have a meaningful English title
                if english_title and len(english_title) > 5:
                    title = english_title
                    logger.info(f"Using English parts from title: '{title}'")
                else:
                    # Try to extract job role from URL
                    url_path = urlparse(job_url).path.lower()
                    for role in job_roles:
                        if role.lower() in url_path:
                            title = role
                            logger.info(f"Extracted job role from URL: '{title}'")
                            break
                    
                    # If we still don't have a title, use the original
                    if title == "Unknown Title":
                        title = original_title
                        logger.info(f"Using original title: '{title}'")
            
            # Extract company name
            company_selectors = ['[class*="company-name"]', 'a.company-name', 'div.company-name', '[class*="company"]']
            company_tag = None
            for selector in company_selectors:
                company_tag = soup.select_one(selector)
                if company_tag:
                    break
            company = company_tag.get_text(strip=True) if company_tag else 'Unknown Company'
            
            # Extract location
            location_selectors = ['[class*="job-location"]', 'div.job-location', '[class*="location"]']
            location_tag = None
            for selector in location_selectors:
                location_tag = soup.select_one(selector)
                if location_tag:
                    break
            location = location_tag.get_text(strip=True) if location_tag else ''
            
            # Extract job description
            desc_selectors = ['[class*="job-description"]', 'div.job-description', '[class*="description"]', 'article', 'div.details']
            description_tag = None
            for selector in desc_selectors:
                description_tag = soup.select_one(selector)
                if description_tag:
                    break
                    
            # Process the description to extract clean text and prioritize English content
            description = ""
            if description_tag:
                # Check if it's HTML content
                if hasattr(description_tag, 'get_text'):
                    # Get all text content
                    full_text = description_tag.get_text(separator='\n', strip=True)
                    
                    # Extract paragraphs with primarily English content
                    paragraphs = full_text.split('\n')
                    english_paragraphs = []
                    
                    for para in paragraphs:
                        # Skip empty paragraphs
                        if not para.strip():
                            continue
                            
                        # Count English vs non-English characters
                        english_chars = sum(1 for char in para if char.isalpha() and ord(char) < 128)
                        total_chars = sum(1 for char in para if char.strip())
                        
                        # If at least 60% of characters are English, include the paragraph
                        if total_chars > 0 and english_chars / total_chars > 0.6:
                            english_paragraphs.append(para.strip())
                        # If paragraph contains numbers/symbols with some English, include it too
                        elif any(char.isalpha() and ord(char) < 128 for char in para):
                            english_paragraphs.append(para.strip())
                    
                    if english_paragraphs:
                        description = '\n\n'.join(english_paragraphs)
                    else:
                        # If no English paragraphs found, use the full text
                        description = full_text
                        
                    # If description seems too short, try getting the HTML
                    if len(description) < 100:
                        # Try preserving some HTML structure but clean it up
                        description = str(description_tag)
                else:
                    description = str(description_tag)
            
            # Extract salary range with improved detection
            salary_range = ""
            
            # Method 1: Look for specific salary selectors
            salary_selectors = ['[class*="job-salary"]', 'div.job-salary', '[class*="salary"]', '[class*="compensation"]']
            salary_tag = None
            for selector in salary_selectors:
                salary_tag = soup.select_one(selector)
                if salary_tag:
                    salary_range = salary_tag.get_text(strip=True)
                    logger.info(f"Found salary with selector: {salary_range}")
                    break
                    
            # Method 2: If no salary found, look for salary patterns in the page text
            if not salary_range:
                # Look for salary in the description or title
                salary_patterns = [
                    r'\$\s*\d+[\d,.]*\s*(?:-\s*\$?\s*\d+[\d,.]*)?(?:\s*[kK])?(?:\s*(?:per|a|\/)\s*(?:month|year|annum|mo|yr))?',
                    r'(?:PHP|₱|Php)\s*\d+[\d,.]*\s*(?:-\s*(?:PHP|₱|Php)?\s*\d+[\d,.]*)?(?:\s*[kK])?(?:\s*(?:per|a|\/)\s*(?:month|year|annum|mo|yr))?',
                    r'\d+[\d,.]*\s*(?:-\s*\d+[\d,.]*)?(?:\s*[kK])?(?:\s*(?:USD|SGD|EUR|GBP|AUD))?(?:\s*(?:per|a|\/)\s*(?:month|year|annum|mo|yr))?',
                    r'(?:USD|SGD|EUR|GBP|AUD)\s*\d+[\d,.]*\s*(?:-\s*(?:USD|SGD|EUR|GBP|AUD)?\s*\d+[\d,.]*)?(?:\s*[kK])?(?:\s*(?:per|a|\/)\s*(?:month|year|annum|mo|yr))?'
                ]
                
                # Search in original title first (often contains salary info)
                for pattern in salary_patterns:
                    salary_match = re.search(pattern, original_title, re.IGNORECASE)
                    if salary_match:
                        salary_range = salary_match.group(0)
                        logger.info(f"Found salary in title: {salary_range}")
                        break
                
                # If still no salary, search in description
                if not salary_range and description:
                    for pattern in salary_patterns:
                        salary_match = re.search(pattern, description, re.IGNORECASE)
                        if salary_match:
                            salary_range = salary_match.group(0)
                            logger.info(f"Found salary in description: {salary_range}")
                            break
                            
                # Search entire page content as last resort
                if not salary_range:
                    page_text = soup.get_text()
                    for pattern in salary_patterns:
                        salary_match = re.search(pattern, page_text, re.IGNORECASE)
                        if salary_match:
                            salary_range = salary_match.group(0)
                            logger.info(f"Found salary in page text: {salary_range}")
                            break
            
            # Extract job type with expanded patterns
            job_type = ""
            job_type_selectors = ['[class*="job-type"]', 'div.job-type', '[class*="employment-type"]']
            job_type_tag = None
            for selector in job_type_selectors:
                job_type_tag = soup.select_one(selector)
                if job_type_tag:
                    job_type = job_type_tag.get_text(strip=True)
                    break
                    
            # If no job type found, try to extract from description or title
            if not job_type:
                job_type_patterns = [
                    r'\b(full[\s\-]?time|part[\s\-]?time|contract|freelance|temporary|internship)\b',
                    r'\b(ft|pt)\b'
                ]
                
                # Check title first
                for pattern in job_type_patterns:
                    job_type_match = re.search(pattern, original_title, re.IGNORECASE)
                    if job_type_match:
                        job_type = job_type_match.group(0)
                        break
                        
                # Then check description
                if not job_type and description:
                    for pattern in job_type_patterns:
                        job_type_match = re.search(pattern, description[:500], re.IGNORECASE)
                        if job_type_match:
                            job_type = job_type_match.group(0)
                            break
            
            # Extract requirements - look for a requirements section
            requirements = ""
            req_patterns = [
                r'(?:requirements|qualifications)[\s\:]+([^#]+?)(?:\n\n|\n\s*\n|\n\s*\w+\s*\:|\Z)',
                r'(?:what you need|what we require|what you\'ll need)[\s\:]+([^#]+?)(?:\n\n|\n\s*\n|\n\s*\w+\s*\:|\Z)'
            ]
            
            for pattern in req_patterns:
                req_match = re.search(pattern, description, re.IGNORECASE)
                if req_match:
                    requirements = req_match.group(1).strip()
                    break
            
            # Extract responsibilities
            responsibilities = ""
            resp_patterns = [
                r'(?:responsibilities|duties|what you\'ll do)[\s\:]+([^#]+?)(?:\n\n|\n\s*\n|\n\s*\w+\s*\:|\Z)',
                r'(?:job description|role|position)[\s\:]+([^#]+?)(?:\n\n|\n\s*\n|\n\s*\w+\s*\:|\Z)'
            ]
            
            for pattern in resp_patterns:
                resp_match = re.search(pattern, description, re.IGNORECASE)
                if resp_match:
                    responsibilities = resp_match.group(1).strip()
                    break
            
            # Extract skills
            skills = ""
            skills_patterns = [
                r'(?:skills|skill requirements|technical skills)[\s\:]+([^#]+?)(?:\n\n|\n\s*\n|\n\s*\w+\s*\:|\Z)',
                r'(?:you have|you possess|candidate has)[\s\:]+([^#]+?)(?:\n\n|\n\s*\n|\n\s*\w+\s*\:|\Z)'
            ]
            
            for pattern in skills_patterns:
                skills_match = re.search(pattern, description, re.IGNORECASE)
                if skills_match:
                    skills = skills_match.group(1).strip()
                    break
            
            # Log if we found a better title
            if title != "Unknown Title":
                logger.info(f"Found actual job title: {title}")
            
            # Format the job type properly for storage
            formatted_job_type = self._normalize_job_type(job_type)
            
            return {
                'title': title,
                'original_title': original_title,  # Keep the original title for reference
                'company': company,
                'location': location,
                'description': description,
                'source_id': job_id,
                'job_type': formatted_job_type,
                'salary_range': salary_range,
                'requirements': requirements,
                'responsibilities': responsibilities,
                'skills': skills,
                'url': job_url,
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when fetching job details: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return {}
    
    def _parse_date(self, date_text: str) -> datetime:
        """
        Parse relative date strings to datetime objects.
        
        Args:
            date_text: String representing posting date (e.g., 'Posted 3 days ago')
            
        Returns:
            Datetime object
        """
        now = timezone.now()
        
        if not date_text:
            return now
            
        # Parse relative dates
        if 'just posted' in date_text.lower():
            return now
        elif 'today' in date_text.lower():
            return now
        elif 'yesterday' in date_text.lower():
            return now - timedelta(days=1)
            
        # Parse "X days ago", "X months ago", etc.
        days_match = re.search(r'(\d+)\s*day', date_text, re.IGNORECASE)
        if days_match:
            days = int(days_match.group(1))
            return now - timedelta(days=days)
            
        weeks_match = re.search(r'(\d+)\s*week', date_text, re.IGNORECASE)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return now - timedelta(weeks=weeks)
            
        months_match = re.search(r'(\d+)\s*month', date_text, re.IGNORECASE)
        if months_match:
            months = int(months_match.group(1))
            # Approximate month as 30 days
            return now - timedelta(days=30 * months)
            
        years_match = re.search(r'(\d+)\s*year', date_text, re.IGNORECASE)
        if years_match:
            years = int(years_match.group(1))
            # Approximate year as 365 days
            return now - timedelta(days=365 * years)
            
        # If we can't parse the date, return the current time
        return now

    def _normalize_job_type(self, job_type: str) -> str:
        """
        Normalize job type formatting.
        
        Args:
            job_type: String representing job type
            
        Returns:
            Normalized job type string
        """
        # Convert job type to title case
        normalized_job_type = job_type.title()
        
        # Remove extra spaces and normalize job type
        normalized_job_type = re.sub(r'\s+', ' ', normalized_job_type).strip()
        
        return normalized_job_type