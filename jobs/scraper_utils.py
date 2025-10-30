import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, quote_plus
from django.core.cache import cache
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class BossJobScraper:
    def __init__(self):
        self.base_url = "https://bossjob.ph"
        self.search_url = "https://bossjob.ph/en-us/jobs-hiring"
        self.session = requests.Session()
        # Default headers tuned to look like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
        })
        self.request_delay = 2  # 2 seconds between requests
        self.last_request_time = 0
    
    def _throttle_request(self):
        """Implement request throttling to be respectful to the website"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_cache_key(self, keyword: str, location: str) -> str:
        """Generate cache key for the search results"""
        return f"bossjob_search_{keyword.lower().replace(' ', '_')}_{location.lower().replace(' ', '_')}"
    
    def _get_region_from_location(self, location: str) -> str:
        """Map location to region for BossJob.ph URL structure"""
        location_lower = location.lower()
        
        # Common region mappings for Philippines
        region_mapping = {
            'manila': 'ncr',
            'quezon city': 'ncr', 
            'makati': 'ncr',
            'taguig': 'ncr',
            'pasig': 'ncr',
            'mandaluyong': 'ncr',
            'cebu': 'central-visayas',
            'davao': 'davao-region',
            'iloilo': 'western-visayas',
            'baguio': 'cordillera-administrative-region',
            'cagayan de oro': 'northern-mindanao',
            'zamboanga': 'zamboanga-peninsula'
        }
        
        # Check for exact matches first
        for city, region in region_mapping.items():
            if city in location_lower:
                return region
        
        # Default to ncr (National Capital Region) if no match found
        return 'ncr'
    
    def search_jobs(self, keyword: str, location: str, use_cache: bool = True) -> Dict:
        """Search for jobs on BossJob.ph"""
        cache_key = self._get_cache_key(keyword, location)
        
        # Check cache first (cache for 30 minutes)
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached results for {keyword} in {location}")
                return cached_result
        
        try:
            # Throttle the request
            self._throttle_request()
            
            # Prepare search parameters using BossJob.ph URL structure
            # Format: /en-us/jobs-hiring/{keyword}-jobs-in-{location}
            keyword_formatted = keyword.lower().replace(' ', '%20')
            location_formatted = location.lower().replace(' ', '-')
            
            # Build the search URL in BossJob.ph format
            search_path = f"{keyword_formatted}-jobs-in-{location_formatted}"
            full_search_url = f"{self.search_url}/{search_path}"
            
            params = {
                'location': location_formatted,
                'region': self._get_region_from_location(location)
            }
            
            logger.info(f"Searching BossJob.ph for '{keyword}' in '{location}' using URL: {full_search_url}")
            
            # Make the request with a plausible Referer
            headers = {'Referer': f"{self.base_url}/"}
            response = self.session.get(full_search_url, params=params, headers=headers, timeout=12)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            jobs = self._extract_jobs(soup, keyword)
            
            # Collect debugging information with updated selectors
            debug_info = {
                'url_accessed': f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}",
                'response_status': response.status_code,
                'response_size': len(response.content),
                'job_elements_found': len(soup.select('.index_pc_listItem__bBJQ5, .yolo-technology-jobCard, div[data-sentry-component="JobCardPc"], .job-card, .job-item')),
                'total_elements_parsed': len(soup.find_all(['div', 'article'])),
                'selectors_tried': ['.index_pc_listItem__bBJQ5', '.yolo-technology-jobCard', 'div[data-sentry-component="JobCardPc"]', '.job-card', '.job-item'],
                'jobs_extracted': len(jobs)
            }
            
            result = {
                'success': True,
                'jobs': jobs,
                'total_found': len(jobs),
                'keyword': keyword,
                'location': location,
                'message': f"Found {len(jobs)} job(s) for '{keyword}' in '{location}'",
                'debug_info': debug_info
            }
            
            # Cache the results for 30 minutes
            if use_cache:
                cache.set(cache_key, result, 1800)
            
            return result
            
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            # If blocked (403), try a softer fallback once with different headers
            if status == 403:
                try:
                    self._throttle_request()
                    alt_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': f'{self.base_url}/en-us/jobs-hiring',
                        'Cache-Control': 'no-cache',
                    }
                    resp2 = self.session.get(full_search_url, params=params, headers=alt_headers, timeout=12)
                    if resp2.status_code == 200:
                        soup = BeautifulSoup(resp2.content, 'html.parser')
                        jobs = self._extract_jobs(soup, keyword)
                        result = {
                            'success': True,
                            'jobs': jobs,
                            'total_found': len(jobs),
                            'keyword': keyword,
                            'location': location,
                            'message': f"Found {len(jobs)} job(s) for '{keyword}' in '{location}'",
                            'debug_info': {
                                'url_accessed': f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}",
                                'response_status': resp2.status_code,
                                'note': '403 recovered with alternate headers',
                            }
                        }
                        if use_cache:
                            cache.set(cache_key, result, 1800)
                        return result
                except requests.RequestException:
                    pass

            error_details = {
                'error_type': 'HTTP Error',
                'error_message': str(e),
                'url_attempted': f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}",
                'status_code': status or 'N/A'
            }
            logger.error(f"HTTP error while scraping BossJob.ph: {error_details}")
            return {
                'success': False,
                'jobs': [],
                'total_found': 0,
                'error': 'Access blocked by source (HTTP 403). Please try again later.',
                'message': 'The source temporarily denied access (403).',
                'fallback_url': f"{self.search_url}/{search_path}",
                'debug_info': error_details
            }
        except requests.exceptions.RequestException as e:
            error_details = {
                'error_type': 'Connection Error',
                'error_message': str(e),
                'url_attempted': f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}",
                'status_code': getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'
            }
            logger.error(f"Request error while scraping BossJob.ph: {error_details}")
            return {
                'success': False,
                'jobs': [],
                'total_found': 0,
                'error': 'Failed to connect to BossJob.ph. Please try again later.',
                'message': 'Connection error occurred',
                'debug_info': error_details
            }
        except Exception as e:
            error_details = {
                'error_type': 'Parsing Error',
                'error_message': str(e),
                'response_status': getattr(response, 'status_code', 'N/A') if 'response' in locals() else 'N/A',
                'response_length': len(getattr(response, 'content', '')) if 'response' in locals() else 0
            }
            logger.error(f"Unexpected error while scraping BossJob.ph: {error_details}")
            return {
                'success': False,
                'jobs': [],
                'total_found': 0,
                'error': 'An unexpected error occurred while fetching jobs.',
                'message': 'Scraping error occurred',
                'debug_info': error_details
            }
    
    def _extract_jobs(self, soup: BeautifulSoup, keyword: str = '') -> List[Dict]:
        """Extract job information from the parsed HTML with deduplication"""
        jobs = []
        seen_jobs = set()  # Track unique jobs to prevent duplicates
        
        # Updated selectors for BossJob.ph current structure (2024)
        # BossJob.ph uses Next.js with specific CSS module classes
        job_selectors = [
            '.index_pc_listItem__bBJQ5',  # Main job card container
            '.yolo-technology-jobCard',   # Alternative job card class
            'div[data-sentry-component="JobCardPc"]',  # Sentry component selector
            '.job-card',  # Fallback
            '.job-item',  # Fallback
            '.job-listing',  # Fallback
            '[data-job-id]',  # Fallback
            'div[class*="listItem"]',  # Pattern match
            'div[class*="jobCard"]'   # Pattern match
        ]
        
        job_elements = []
        for selector in job_selectors:
            job_elements = soup.select(selector)
            if job_elements:
                break
        
        # If no specific job containers found, try to find job listings in a more generic way
        if not job_elements:
            # Look for common patterns in job listings
            job_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['job', 'position', 'vacancy', 'listing']
            ))
        
        # Limit to first 15 results
        job_elements = job_elements[:15]
        
        extracted_jobs = 0
        filtered_jobs = 0
        
        for job_element in job_elements:
            try:
                job_data = self._extract_job_data(job_element)
                if job_data and job_data.get('title'):
                    extracted_jobs += 1
                    
                    # Create unique identifier for deduplication
                    job_signature = self._create_job_signature(job_data)
                    
                    # Skip if we've already seen this job
                    if job_signature in seen_jobs:
                        logger.debug(f"Skipping duplicate job: {job_data.get('title')} at {job_data.get('company')}")
                        continue
                    
                    seen_jobs.add(job_signature)
                    
                    # Filter jobs based on keyword relevance
                    if self._is_job_relevant(job_data, keyword):
                        jobs.append(job_data)
                    else:
                        filtered_jobs += 1
                        logger.debug(f"Filtered out irrelevant job: {job_data.get('title')}")
            except Exception as e:
                logger.warning(f"Error extracting job data: {str(e)}")
                continue
        
        # Log detailed information about the scraping attempt
        logger.info(f"Scraping completed. Found {len(jobs)} relevant jobs from {extracted_jobs} extracted jobs ({filtered_jobs} filtered out) from {len(job_elements)} elements")
        if not jobs:
            logger.warning(f"No relevant jobs found from {extracted_jobs} extracted jobs ({filtered_jobs} filtered out) from {len(job_elements)} job elements")
            if extracted_jobs > 0:
                logger.info(f"Jobs were found but filtered out as irrelevant to keyword '{keyword}'")
            logger.debug(f"HTML content preview: {str(soup)[:500]}...")

        return jobs
    
    def _create_job_signature(self, job_data: Dict) -> str:
        """Create a unique signature for a job to detect duplicates"""
        # Normalize text for comparison
        title = (job_data.get('title', '') or '').strip().lower()
        company = (job_data.get('company', '') or '').strip().lower()
        location = (job_data.get('location', '') or '').strip().lower()
        
        # Remove common variations and normalize
        title = title.replace('job title not available', '').strip()
        company = company.replace('company not specified', '').strip()
        location = location.replace('location not specified', '').strip()
        
        # Create signature from title + company + location
        signature = f"{title}|{company}|{location}"
        return signature
    
    def _is_valid_job_url(self, url: str) -> bool:
        """Validate if a URL is a valid job URL for BossJob.ph"""
        if not url or url in ['#', 'javascript:void(0)', 'javascript:', 'mailto:', '#no-url-found']:
            return False
        
        # Remove common invalid patterns
        invalid_patterns = ['#', 'javascript:', 'mailto:', 'tel:', 'void(0)', 'data:', 'blob:']
        url_lower = url.lower()
        
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False
        
        # Check for minimum URL length and structure
        if len(url.strip()) < 3:
            return False
        
        # BossJob.ph specific validation - prefer URLs that look like job pages
        if any(pattern in url_lower for pattern in ['/job/', '/position/', '/jobs/', 'bossjob.ph']):
            return True
        
        # Allow other valid URLs but with lower priority
        if url.startswith(('http://', 'https://', '/')):
            return True
            
        return False
    
    def _extract_job_data(self, job_element) -> Optional[Dict]:
        """Extract individual job data from a job element"""
        try:
            # Updated title selectors for BossJob.ph structure
            title_selectors = [
                '.index_pc_jobHireTopTitle__zVsw_ span',  # Main title selector
                '.index_pc_jobHireTopTitle__zVsw_',       # Title container
                'h3.index_pc_jobHireTopTitle__zVsw_ span', # Specific h3 title
                '.job-title',  # Fallback
                '.position-title',  # Fallback
                'h1', 'h2', 'h3', 'h4',  # Fallback
                '[data-job-title]',  # Fallback
                '.job-name',  # Fallback
                'a[href*="job"]'  # Fallback
            ]
            title = self._extract_text_by_selectors(job_element, title_selectors)
            
            # Skip if title is too generic or empty
            if not title or len(title.strip()) < 3:
                return None
                
            # Updated company selectors for BossJob.ph structure
            company_selectors = [
                '.index_pc_jobHireRecruiterName__ROjos',  # Main company name
                '.index_pc_listCompany__jDFjq p',         # Company paragraph
                '.index_pc_listCompanyRecruiter__40_9t p', # Recruiter company
                'img[alt]',  # Company logo alt text as fallback
                '.company', '.company-name', '.employer',  # Fallbacks
                '[data-company]', '.job-company'  # Fallbacks
            ]
            company = self._extract_text_by_selectors(job_element, company_selectors)
            
            # Updated location selectors for BossJob.ph structure
            location_selectors = [
                '.index_pc_jobCardLocationItem__Gzujh',  # Location tags
                '.index_pc_listTag__c_IF4 span',         # All tags (includes location)
                'span[class*="location"]',  # Fallback
                '.location', '.job-location', '.address',  # Fallbacks
                '[data-location]', '.location-info'  # Fallbacks
            ]
            location = self._extract_location_text(job_element, location_selectors)
            
            # Updated description selectors for BossJob.ph structure
            desc_selectors = [
                '.index_pc_listTag__c_IF4',              # Job tags as description
                '.index_pc_jobCardLocationItem__Gzujh',  # Individual tags
                '.index_pc_container__AiU7S',            # Container with salary info
                '.description', '.job-description',      # Fallbacks
                '.summary', '.job-summary', '.content',  # Fallbacks
                'p', '.card-text'  # Fallbacks
            ]
            description = self._extract_text_by_selectors(job_element, desc_selectors)
            
            # Updated salary selectors for BossJob.ph structure
            salary_selectors = [
                '.index_pc_salaryText__k3HPE',  # Main salary text
                '.index_pc_salary__j_ar2',      # Salary container
                '.index_pc_month__DVKin',       # Monthly indicator
                '.salary', '.wage', '.pay',     # Fallbacks
                '[data-salary]'  # Fallback
            ]
            salary = self._extract_text_by_selectors(job_element, salary_selectors)
            
            # Try to extract URL
            url = self._extract_job_url(job_element)
            
            return {
                'title': title or 'Job Title Not Available',
                'company': company or 'Company Not Specified',
                'location': location or 'Location Not Specified',
                'description': description or 'No description available',
                'salary': salary or 'Salary not disclosed',
                'url': url or '#'
            }
        except Exception as e:
            logger.warning(f"Error extracting job data: {str(e)}")
            return None
    
    def _extract_text_by_selectors(self, element, selectors: List[str]) -> str:
        """Try multiple selectors to extract text with enhanced logic"""
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                # Get text and clean it
                text = found.get_text(strip=True, separator=' ')
                if text:
                    # Clean up extra whitespace and normalize
                    text = ' '.join(text.split())
                    # Skip very short or generic text
                    if len(text) > 2 and text.lower() not in ['n/a', 'tbd', 'na', '...']:
                        return text
        
        # If no specific selector worked, try to get any text from the element
        if element:
            all_text = element.get_text(strip=True, separator=' ')
            if all_text:
                all_text = ' '.join(all_text.split())
                # Return first meaningful sentence or phrase (up to 200 chars)
                if len(all_text) > 2:
                    return all_text[:200] + ('...' if len(all_text) > 200 else '')
        
        return ''
    
    def _extract_location_text(self, element, selectors: List[str]) -> str:
        """Extract location text while filtering out non-location tags"""
        # Common non-location tags to filter out
        non_location_keywords = [
            'great perks', 'fresh grads welcome', 'quick responder', 'urgent', 
            'be an early applicant', 'full-time', 
            'part-time', 'contract', 'permanent', 'temporary', 'monthly', 'weekly',
            'yr exp', 'experience', 'welcome', 'not required', 'fresh graduate', 
            'student', 'no exp', 'exp required', 'bachelor', 'edu not required'
        ]
        
        # Common location keywords to prioritize
        location_keywords = [
            'manila', 'cebu', 'davao', 'makati', 'taguig', 'pasig', 'quezon city',
            'bgc', 'ortigas', 'alabang', 'ncr', 'metro manila', 'philippines',
            'on-site', 'remote', 'hybrid'
        ]
        
        for selector in selectors:
            elements = element.select(selector)  # Get all matching elements
            for found in elements:
                text = found.get_text(strip=True, separator=' ')
                if text:
                    text_clean = ' '.join(text.split())
                    text_lower = text_clean.lower()
                    
                    # Skip if it's a non-location keyword
                    if any(keyword in text_lower for keyword in non_location_keywords):
                        continue
                    
                    # Look for "On-site - City" pattern
                    if 'on-site -' in text_lower:
                        return text_clean
                    
                    # Prioritize if it contains location keywords
                    if any(keyword in text_lower for keyword in location_keywords):
                        return text_clean.title()  # Return with proper capitalization
                    
                    # If it's short and doesn't contain obvious non-location words, consider it
                    if len(text_clean) < 50 and not any(word in text_lower for word in ['perks', 'grads', 'responder', 'applicant']):
                        return text_clean.title()
        
        return 'Location Not Specified'
    
    def _extract_job_url(self, job_element) -> str:
        """Extract job URL from the job element with enhanced selectors and validation for BossJob.ph"""
        # BossJob.ph 2024 structure - jobs are clickable cards but may not have direct links
        # The site uses SPA navigation, so we need to construct URLs or find data attributes
        link_selectors = [
            # Look for any links within the job card
            'a[href]',  # Any link
            # BossJob.ph specific patterns
            'a[href*="/job/"]',  # Direct job page links
            'a[href*="/position/"]',  # Position page links
            'a[href*="/jobs/"]',  # Jobs page links
            # Data attributes that might contain job IDs
            '[data-job-id]',  # Job ID data attributes
            '[data-position-id]',  # Position ID data attributes
            '[data-sentry-component="JobCardPc"]',  # Component with potential data
            # Title links
            '.index_pc_jobHireTopTitle__zVsw_ a[href]',
            'h3 a[href]', 'h2 a[href]', 'h1 a[href]',
        ]
        
        valid_urls = []
        debug_info = []
        
        # First, try to find BossJob.ph specific job URLs
        for selector in link_selectors:
            links = job_element.select(selector)
            for link in links:
                href = link.get('href')
                data_job_id = link.get('data-job-id')
                data_position_id = link.get('data-position-id')
                
                debug_info.append(f"Selector '{selector}': href='{href}', data-job-id='{data_job_id}', data-position-id='{data_position_id}'")
                
                # If we have data attributes, try different URL patterns
                if data_job_id:
                    # Try multiple URL patterns for BossJob.ph
                    possible_urls = [
                        f"{self.base_url}/job/{data_job_id}",
                        f"{self.base_url}/en-us/job/{data_job_id}",
                        f"{self.base_url}/jobs/{data_job_id}",
                        f"{self.base_url}/position/{data_job_id}"
                    ]
                    for url in possible_urls:
                        valid_urls.append(url)
                        debug_info.append(f"Constructed URL from data-job-id: {url}")
                elif data_position_id:
                    # Try multiple URL patterns for position IDs
                    possible_urls = [
                        f"{self.base_url}/position/{data_position_id}",
                        f"{self.base_url}/en-us/position/{data_position_id}",
                        f"{self.base_url}/job/{data_position_id}",
                        f"{self.base_url}/jobs/{data_position_id}"
                    ]
                    for url in possible_urls:
                        valid_urls.append(url)
                        debug_info.append(f"Constructed URL from data-position-id: {url}")
                elif href and self._is_valid_job_url(href):
                    # Clean and construct the URL
                    href = href.strip()
                    if href.startswith('http'):
                        # Validate that it's actually a BossJob.ph URL
                        if 'bossjob.ph' in href.lower():
                            valid_urls.append(href)
                            debug_info.append(f"Added absolute BossJob URL: {href}")
                    elif href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                        valid_urls.append(full_url)
                        debug_info.append(f"Added relative URL: {full_url}")
                    elif href and not href.startswith('#'):
                        # Relative URL
                        full_url = urljoin(self.base_url, '/' + href.lstrip('/'))
                        valid_urls.append(full_url)
                        debug_info.append(f"Added constructed URL: {full_url}")
        
        # Return the first valid URL found, prioritizing job-specific URLs
        if valid_urls:
            # Sort URLs to prioritize job-specific patterns
            job_priority_patterns = ['/job/', '/position/', '/jobs/']
            prioritized_urls = []
            other_urls = []
            
            for url in valid_urls:
                if any(pattern in url.lower() for pattern in job_priority_patterns):
                    prioritized_urls.append(url)
                else:
                    other_urls.append(url)
            
            final_urls = prioritized_urls + other_urls
            logger.debug(f"Found {len(valid_urls)} valid URLs. Prioritized: {len(prioritized_urls)}. Debug info: {'; '.join(debug_info)}")
            return final_urls[0]
        
        # Fallback: Look for any clickable elements that might lead to job details
        fallback_selectors = [
            'a[href]:not([href="#"]):not([href="javascript:void(0)"])',
            '[onclick*="job"]',
            '[onclick*="position"]',
            'button[data-job-id]',
            'div[data-job-id]'
        ]
        
        for selector in fallback_selectors:
            elements = job_element.select(selector)
            for element in elements:
                href = element.get('href')
                onclick = element.get('onclick')
                data_job_id = element.get('data-job-id')
                
                debug_info.append(f"Fallback selector '{selector}': href='{href}', onclick='{onclick}', data-job-id='{data_job_id}'")
                
                if data_job_id:
                    # Try the most common pattern first
                    constructed_url = f"{self.base_url}/job/{data_job_id}"
                    logger.debug(f"Fallback: Constructed URL from data-job-id: {constructed_url}")
                    return constructed_url
                elif href and self._is_valid_job_url(href):
                    if href.startswith('http') and 'bossjob.ph' in href.lower():
                        logger.debug(f"Fallback: Found absolute BossJob URL: {href}")
                        return href
                    elif href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                        logger.debug(f"Fallback: Found relative URL: {full_url}")
                        return full_url
        
        # If no valid URL found, log debug info and return the search page URL
        logger.warning(f"No valid job URL found. Debug info: {'; '.join(debug_info)}")
        
        # For SPA sites like BossJob.ph, return the main jobs page since individual job URLs might not be available
        # Users can still navigate to the specific job from the main page
        return f"{self.base_url}/en-us/jobs-hiring/"
    
    def _is_job_relevant(self, job_data: Dict, keyword: str) -> bool:
        """Check if job is relevant to the search keyword with relaxed filtering"""
        if not keyword:
            return True
            
        keyword_lower = keyword.lower()
        
        # Check title, description, and company for keyword relevance
        searchable_text = ' '.join([
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('company', '')
        ]).lower()
        
        # Split keyword into individual words for better matching
        keyword_words = keyword_lower.split()
        
        # More relaxed relevance check - job is relevant if:
        # 1. Any keyword word appears in the searchable text
        # 2. Or if it's a tech-related job and keyword contains tech terms
        # 3. Or if the job title contains common job-related words
        
        for word in keyword_words:
            if len(word) > 2 and word in searchable_text:
                return True
        
        # Additional tech-related keywords for broader matching
        tech_keywords = ['developer', 'programmer', 'engineer', 'analyst', 'designer', 'manager', 'specialist', 'coordinator']
        job_title_lower = job_data.get('title', '').lower()
        
        # If searching for tech roles, be more inclusive
        if any(tech_word in keyword_lower for tech_word in tech_keywords):
            if any(tech_word in job_title_lower for tech_word in tech_keywords):
                return True
        
        # If we're on BossJob.ph and got this far, it's likely relevant since the site already filtered by keyword
        # Be more inclusive for jobs from job boards
        if len(job_data.get('title', '').strip()) > 5:  # Has a meaningful title
            return True
                
        return False
    


# Singleton instance
scraper = BossJobScraper()