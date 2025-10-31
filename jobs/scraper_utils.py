import os
import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, quote_plus
from django.core.cache import cache
from django.conf import settings
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class BossJobScraper:
    def __init__(self):
        self.base_url = "https://bossjob.ph"
        self.search_url = "https://bossjob.ph/en-us/jobs-hiring"
        self.session = requests.Session()
        # Updated headers to better mimic a real modern browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'DNT': '1',
            'Cache-Control': 'max-age=0',
        })
        self.request_delay = 3  # Increased to 3 seconds between requests to be more respectful
        self.last_request_time = 0
        self._initialize_session()
        
        # Selenium config - Enable by default for JS-rendered content
        # Can be disabled by setting SELENIUM_ENABLE=false
        self.enable_selenium = os.getenv('SELENIUM_ENABLE', 'true').lower() == 'true'
        self.selenium_remote_url = os.getenv('SELENIUM_REMOTE_URL')  # e.g., http://selenium:4444/wd/hub
        self.selenium_browser = os.getenv('SELENIUM_BROWSER', 'chrome')
    
    def _initialize_session(self):
        """Initialize session by visiting homepage first to establish cookies and session"""
        try:
            logger.debug("Initializing session by visiting BossJob.ph homepage...")
            self._throttle_request()
            # Visit homepage first to get cookies and establish session
            homepage_response = self.session.get(
                self.base_url,
                timeout=10,
                allow_redirects=True
            )
            if homepage_response.status_code == 200:
                logger.debug("Session initialized successfully")
            else:
                logger.warning(f"Homepage returned status {homepage_response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to initialize session: {str(e)}")
            # Continue anyway, might still work
    
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
        # Normalize inputs to ensure consistent cache keys
        keyword = keyword.strip().lower()
        location = location.strip().lower()
        
        cache_key = self._get_cache_key(keyword, location)
        
        # Check cache first (cache for 30 minutes)
        # Temporarily disable cache to ensure fresh, accurate results for each search
        # TODO: Re-enable cache once we verify searches are working correctly
        use_cache = False  # Disable cache to ensure fresh results
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached results for '{keyword}' in '{location}' (cache key: {cache_key})")
                # Return cached result with updated keyword/location to match what user searched
                cached_result['keyword'] = keyword
                cached_result['location'] = location
                return cached_result
        
        logger.info(f"Performing FRESH search (cache disabled) for '{keyword}' in '{location}' (cache key: {cache_key})")
        
        # Prepare search parameters (outside try block so they're available in exception handler)
        keyword_formatted = keyword.lower().strip().replace(' ', '-')
        location_formatted = location.lower().strip().replace(' ', '-')
        
        # Ensure keyword is not empty
        if not keyword_formatted:
            keyword_formatted = 'general'
        
        # Ensure location is not empty
        if not location_formatted:
            location_formatted = 'philippines'
        
        # BossJob.ph uses the /en-us/onsite-job endpoint with query parameters
        # Format: /en-us/onsite-job?q=KEYWORD&location=X&region=Y
        # The 'q' parameter is the keyword search
        full_search_url = f"{self.base_url}/en-us/onsite-job"
        
        params = {
            'q': keyword,  # Primary keyword parameter (used for search)
            'location': location_formatted,
            'region': self._get_region_from_location(location),
        }
        
        # Log the exact URL being accessed
        full_url_with_params = f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}"
        logger.info(f"Searching BossJob.ph - Keyword: '{keyword}' -> '{keyword_formatted}', Location: '{location}' -> '{location_formatted}'")
        logger.info(f"Search URL: {full_url_with_params}")
        
        try:
            # Throttle the request
            self._throttle_request()
            
            # Make the request with enhanced headers to mimic a real browser navigation
            headers = {
                'Referer': f"{self.base_url}/",
                'Origin': self.base_url,
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-User': '?1',
            }
            # Make request with additional headers (merge with existing session headers)
            request_headers = {**self.session.headers, **headers}
            response = self.session.get(full_search_url, params=params, headers=request_headers, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: Save HTML to file for inspection (only if no jobs found)
            html_sample_saved = False
            
            # Try to extract jobs from embedded JSON first (React/Next.js apps often embed data)
            jobs = self._extract_from_json_scripts(soup, keyword)
            
            # If no jobs from JSON, try HTML extraction
            if len(jobs) == 0:
                jobs = self._extract_jobs(soup, keyword)
            
            # ALWAYS use Selenium for accurate results since BossJob.ph is JS-rendered
            # This ensures we get correct results matching the user's search criteria
            # Skip HTML extraction entirely and go straight to Selenium
            if self.enable_selenium:
                logger.info(f"Using Selenium to fetch accurate results for '{keyword}' in '{location}'...")
                try:
                    selenium_result = self._selenium_fetch(full_search_url, params, keyword, location)
                    if selenium_result and selenium_result.get('success'):
                        selenium_jobs = selenium_result.get('jobs', [])
                        logger.info(f"Selenium found {len(selenium_jobs)} jobs for search: keyword='{keyword}', location='{location}'")
                        
                        # Use Selenium results (more accurate for JS-rendered content)
                        if len(selenium_jobs) > 0:
                            logger.info(f"Returning {len(selenium_jobs)} jobs from Selenium for '{keyword}' in '{location}'")
                            if use_cache:
                                cache.set(cache_key, selenium_result, 1800)
                            return selenium_result
                        else:
                            logger.warning(f"Selenium found 0 jobs for '{keyword}' in '{location}' - URL may be incorrect or page structure changed")
                            # Return empty results with helpful message
                            return {
                                'success': True,
                                'jobs': [],
                                'total_found': 0,
                                'keyword': keyword,
                                'location': location,
                                'message': f"No jobs found for '{keyword}' in '{location}'. The page structure may have changed or the search URL may be incorrect.",
                                'debug_info': selenium_result.get('debug_info', {}) if selenium_result else {}
                            }
                    elif selenium_result and not selenium_result.get('success'):
                        logger.warning(f"Selenium attempt failed for '{keyword}' in '{location}': {selenium_result.get('message', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Selenium fetch failed for '{keyword}' in '{location}': {str(e)}", exc_info=True)
                    logger.warning("Make sure ChromeDriver is installed and accessible in PATH, or set SELENIUM_REMOTE_URL")
            
            # If no jobs found, save HTML sample for debugging
            if len(jobs) == 0:
                try:
                    # Save a sample of the HTML for debugging
                    debug_dir = os.path.join(settings.MEDIA_ROOT, 'scraper_debug')
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = os.path.join(debug_dir, f"bossjob_debug_{int(time.time())}.html")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.warning(f"Saved HTML debug file: {debug_file}")
                    html_sample_saved = True
                except Exception as e:
                    logger.debug(f"Could not save debug HTML: {str(e)}")
            
            # Collect debugging information with updated selectors
            # Try multiple selector patterns to count elements
            test_selectors = [
                '.index_pc_listItem__bBJQ5',
                '.yolo-technology-jobCard',
                'div[data-sentry-component="JobCardPc"]',
                'div[class*="jobCard"]',
                'div[class*="listItem"]',
                '[data-job-id]',
                '[data-testid*="job"]',
                '.job-card',
                '.job-item',
                'article',
                'section[class*="job"]'
            ]
            
            selector_results = {}
            for selector in test_selectors:
                try:
                    count = len(soup.select(selector))
                    if count > 0:
                        selector_results[selector] = count
                except:
                    pass
            
            debug_info = {
                'url_accessed': f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}",
                'response_status': response.status_code,
                'response_size': len(response.content),
                'html_saved_for_debugging': html_sample_saved,
                'selector_results': selector_results,
                'total_elements_parsed': len(soup.find_all(['div', 'article'])),
                'selectors_tried': test_selectors,
                'jobs_extracted': len(jobs),
                'html_preview': response.text[:500] if len(response.text) > 500 else response.text
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
                logger.warning("Received 403 Forbidden, attempting to recover with alternative headers...")
                try:
                    self._throttle_request()
                    # Try visiting homepage again to refresh cookies
                    try:
                        self.session.get(self.base_url, timeout=10, allow_redirects=True)
                        time.sleep(1)  # Small delay after homepage visit
                    except:
                        pass
                    
                    # Try with more conservative headers and different approach
                    alt_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': f'{self.base_url}/en-us/jobs-hiring',
                        'Origin': self.base_url,
                        'Cache-Control': 'max-age=0',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-User': '?1',
                    }
                    # Create a new request with alternative headers
                    resp2 = self.session.get(
                        full_search_url, 
                        params=params, 
                        headers=alt_headers, 
                        timeout=15,
                        allow_redirects=True
                    )
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

                # Selenium fallback if enabled
                if self.enable_selenium and (self.selenium_remote_url or self.selenium_browser):
                    selenium_result = self._selenium_fetch(full_search_url, params, keyword, location)
                    if selenium_result and selenium_result.get('success'):
                        if use_cache:
                            cache.set(cache_key, selenium_result, 1800)
                        return selenium_result

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
                'fallback_url': f"{self.search_url}",
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
        
        # Debug: Log HTML structure to understand what we're working with
        logger.debug("Attempting to extract jobs from HTML...")
        
        # Try to find main content container first
        main_containers = soup.select('main, [role="main"], .main-content, #main-content, .container, .content')
        logger.debug(f"Found {len(main_containers)} main containers")
        
        # Updated selectors for BossJob.ph - try multiple patterns
        # BossJob.ph uses Next.js with dynamically generated CSS classes
        job_selectors = [
            # Try attribute selectors first (more stable)
            '[data-testid*="job"]',
            '[data-testid*="Job"]',
            '[data-cy*="job"]',
            '[data-job-id]',
            '[data-position-id]',
            '[data-sentry-component="JobCardPc"]',
            
            # Try class patterns (Next.js CSS modules)
            'div[class*="jobCard"]',
            'div[class*="JobCard"]',
            'div[class*="listItem"]',
            'div[class*="ListItem"]',
            'div[class*="job-item"]',
            'div[class*="JobItem"]',
            '.index_pc_listItem__bBJQ5',
            '.yolo-technology-jobCard',
            
            # Generic semantic selectors
            'article[class*="job"]',
            'section[class*="job"]',
            'div[class*="listing"]',
            
            # Common class names
            '.job-card',
            '.job-item',
            '.job-listing',
            '.job-post',
            '.position-card',
            '.vacancy-card',
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                logger.debug(f"Found {len(elements)} job elements using selector: {selector}")
                job_elements = elements
                break
        
        # If no specific job containers found, try to find job listings in a more generic way
        if not job_elements:
            logger.debug("No jobs found with specific selectors, trying generic patterns...")
            
            # Look for divs with job-related attributes
            job_elements = soup.find_all(['div', 'article'], attrs={'data-testid': lambda x: x and 'job' in str(x).lower()})
            if job_elements:
                logger.debug(f"Found {len(job_elements)} jobs using data-testid pattern")
            
            # If still nothing, look for elements with job-related classes
            if not job_elements:
                job_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                    keyword in str(x).lower() for keyword in ['job', 'position', 'vacancy', 'listing', 'hire', 'career']
                ))
                if job_elements:
                    logger.debug(f"Found {len(job_elements)} jobs using class pattern matching")
            
            # Last resort: look for links containing /job/ or /position/
            if not job_elements:
                job_links = soup.find_all('a', href=lambda x: x and ('/job/' in str(x) or '/position/' in str(x)))
                # Get parent elements of these links
                job_elements = [link.find_parent(['div', 'article', 'li']) for link in job_links if link.find_parent(['div', 'article', 'li'])]
                job_elements = [e for e in job_elements if e]  # Remove None values
                if job_elements:
                    logger.debug(f"Found {len(job_elements)} jobs using link pattern")
        
        # Debug: Log what we found
        if not job_elements:
            # Log sample HTML to help debug
            logger.warning("No job elements found. Sample HTML structure:")
            # Log first 2000 chars of body
            body = soup.find('body')
            if body:
                logger.warning(f"Body HTML sample (first 2000 chars): {str(body)[:2000]}")
            # Log common container patterns
            all_divs = soup.find_all('div', limit=20)
            logger.debug(f"Sample div classes found: {[div.get('class') for div in all_divs if div.get('class')]}")
        
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
    
    def _extract_from_json_scripts(self, soup: BeautifulSoup, keyword: str = '') -> List[Dict]:
        """Try to extract job data from JSON-LD or embedded JSON scripts in the page"""
        jobs = []
        try:
            # Look for JSON-LD structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    # Look for JobPosting schema
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        jobs.append({
                            'title': data.get('title', ''),
                            'company': data.get('hiringOrganization', {}).get('name', ''),
                            'location': data.get('jobLocation', {}).get('address', {}).get('addressLocality', ''),
                            'description': data.get('description', ''),
                            'url': data.get('url', ''),
                            'salary': data.get('baseSalary', {})
                        })
                except:
                    continue
            
            # Look for embedded JSON in script tags (common in React/Next.js apps)
            script_tags = soup.find_all('script')
            for script in script_tags:
                if not script.string:
                    continue
                script_text = script.string.strip()
                
                # Try to find JSON data in the script
                # Common patterns: __NEXT_DATA__, window.__INITIAL_STATE__, etc.
                if any(pattern in script_text for pattern in ['__NEXT_DATA__', '__INITIAL_STATE__', 'jobs', 'jobList', 'jobItems']):
                    try:
                        import json
                        import re
                        
                        # Try to extract __NEXT_DATA__ object
                        if '__NEXT_DATA__' in script_text:
                            next_data_match = re.search(r'__NEXT_DATA__\s*=\s*(\{.*?\});', script_text, re.DOTALL)
                            if next_data_match:
                                data = json.loads(next_data_match.group(1))
                                jobs_data = self._find_jobs_in_dict(data)
                                if jobs_data:
                                    logger.info(f"Found {len(jobs_data)} jobs in __NEXT_DATA__")
                                    jobs.extend(jobs_data)
                                    continue
                        
                        # Try to extract any JSON object containing "jobs"
                        json_matches = re.finditer(r'\{[^{}]*"jobs"[^{}]*\}', script_text, re.DOTALL)
                        for match in json_matches:
                            try:
                                data = json.loads(match.group())
                                jobs_data = self._find_jobs_in_dict(data)
                                if jobs_data:
                                    logger.info(f"Found {len(jobs_data)} jobs in JSON script")
                                    jobs.extend(jobs_data)
                                    break
                            except:
                                continue
                        
                        # Try to find jobs array directly
                        jobs_array_match = re.search(r'"jobs"\s*:\s*\[(.*?)\]', script_text, re.DOTALL)
                        if jobs_array_match:
                            try:
                                jobs_str = '[' + jobs_array_match.group(1) + ']'
                                jobs_list = json.loads(jobs_str)
                                for job_item in jobs_list:
                                    if isinstance(job_item, dict):
                                        jobs_data = self._find_jobs_in_dict(job_item)
                                        if jobs_data:
                                            jobs.extend(jobs_data)
                            except:
                                pass
                    except Exception as e:
                        logger.debug(f"Could not parse JSON from script: {str(e)}")
                        continue
        except Exception as e:
            logger.debug(f"Error extracting from JSON scripts: {str(e)}")
        
        return jobs
    
    def _find_jobs_in_dict(self, data, max_depth=5):
        """Recursively search for job data in nested dictionaries"""
        if max_depth <= 0:
            return []
        
        jobs = []
        
        if isinstance(data, dict):
            # Check if this dict looks like a job
            if 'title' in data and ('company' in data or 'employer' in data):
                jobs.append({
                    'title': data.get('title', ''),
                    'company': data.get('company') or data.get('employer') or data.get('hiringOrganization', {}).get('name', ''),
                    'location': data.get('location', ''),
                    'description': data.get('description', ''),
                    'url': data.get('url', ''),
                    'salary': data.get('salary', '')
                })
            
            # Look for arrays of jobs
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and ('title' in item or 'jobTitle' in item):
                            jobs.extend(self._find_jobs_in_dict(item, max_depth - 1))
                        elif isinstance(item, dict):
                            jobs.extend(self._find_jobs_in_dict(item, max_depth - 1))
                elif isinstance(value, dict):
                    jobs.extend(self._find_jobs_in_dict(value, max_depth - 1))
        
        elif isinstance(data, list):
            for item in data:
                jobs.extend(self._find_jobs_in_dict(item, max_depth - 1))
        
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
    
    def _selenium_fetch(self, full_search_url: str, params: Dict, keyword: str, location: str) -> Optional[Dict]:
        """Fetch page content using Selenium (Remote or local) and parse jobs.

        Requires env: SELENIUM_ENABLE=true and either SELENIUM_REMOTE_URL or a local driver available.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
        except Exception as imp_err:
            logger.warning(f"Selenium not available: {imp_err}")
            return None

        url = f"{full_search_url}?{urljoin('', '&'.join([f'{k}={v}' for k, v in params.items()]))}"
        
        # Log the exact URL Selenium will navigate to
        logger.info(f"Selenium _selenium_fetch called with:")
        logger.info(f"  - full_search_url: {full_search_url}")
        logger.info(f"  - params: {params}")
        logger.info(f"  - keyword: '{keyword}'")
        logger.info(f"  - location: '{location}'")
        logger.info(f"  - Final URL: {url}")

        driver = None
        try:
            if self.selenium_remote_url:
                if self.selenium_browser.lower() == 'firefox':
                    options = FirefoxOptions()
                    options.add_argument('-headless')
                    driver = webdriver.Remote(command_executor=self.selenium_remote_url, options=options)
                else:
                    options = ChromeOptions()
                    options.add_argument('--headless=new')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--window-size=1280,800')
                    options.add_argument(f"--user-agent={self.session.headers.get('User-Agent')}")
                    driver = webdriver.Remote(command_executor=self.selenium_remote_url, options=options)
            else:
                # Attempt local Chrome if available
                options = ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--start-maximized')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_argument(f"--user-agent={self.session.headers.get('User-Agent')}")
                
                try:
                    # Try using webdriver_manager for automatic driver management
                    try:
                        from selenium.webdriver.chrome.service import Service
                        from webdriver_manager.chrome import ChromeDriverManager
                        service = Service(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=options)
                        logger.info("Using webdriver_manager for ChromeDriver")
                    except ImportError:
                        # Fallback to system ChromeDriver
                        driver = webdriver.Chrome(options=options)
                        logger.info("Using system ChromeDriver")
                except Exception as e:
                    logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
                    # Don't raise - just return None so caller can fall back to HTTP requests
                    driver = None
                    if "cannot find Chrome binary" in str(e):
                        logger.warning("Chrome browser not found. Selenium will be disabled for this request. Install Chrome or set SELENIUM_REMOTE_URL to use a remote Selenium server.")
                    return None  # Return None if driver initialization failed
            
            # Check if driver was successfully initialized
            if driver is None:
                logger.warning("Selenium driver not available, skipping Selenium fetch")
                return None
            
            driver.set_page_load_timeout(30)
            logger.info(f"Selenium navigating to: {url}")
            logger.info(f"Search parameters - Keyword: '{keyword}', Location: '{location}'")
            
            # Navigate to the URL
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Verify we're on the right page by checking URL
            actual_url = driver.current_url
            page_title = driver.title
            logger.info(f"Selenium current URL after navigation: {actual_url}")
            logger.info(f"Selenium page title: {page_title}")
            
            # Verify URL contains our search parameters
            keyword_formatted = keyword.lower().replace(' ', '-')
            location_formatted = location.lower().replace(' ', '-')
            keyword_in_url = keyword_formatted in actual_url.lower()
            location_in_url = location_formatted in actual_url.lower()
            
            if not keyword_in_url or not location_in_url:
                logger.warning(f"WARNING: URL may not match search parameters!")
                logger.warning(f"  Expected keyword '{keyword}' (formatted: '{keyword_formatted}') in URL")
                logger.warning(f"  Expected location '{location}' (formatted: '{location_formatted}') in URL")
                logger.warning(f"  Actual URL: {actual_url}")
                logger.warning(f"  Keyword in URL: {keyword_in_url}, Location in URL: {location_in_url}")
            
            # Wait for common loading indicators to disappear
            try:
                WebDriverWait(driver, 15).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="loading"], [class*="spinner"], [class*="skeleton"]'))
                )
            except:
                pass
            
            # Scroll to trigger lazy loading if present
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Try multiple wait strategies for job elements
            job_found = False
            wait_strategies = [
                (By.CSS_SELECTOR, 'div[class*="jobCard"]'),
                (By.CSS_SELECTOR, 'div[class*="listItem"]'),
                (By.CSS_SELECTOR, '[data-testid*="job"]'),
                (By.CSS_SELECTOR, '[data-job-id]'),
                (By.CSS_SELECTOR, 'article'),
                (By.CSS_SELECTOR, '[class*="job"]'),
                (By.XPATH, "//div[contains(@class, 'job') or contains(@class, 'position')]"),
                (By.XPATH, "//a[contains(@href, '/job/') or contains(@href, '/position/')]"),
            ]
            
            for strategy in wait_strategies:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(strategy)
                    )
                    logger.info(f"Selenium found elements using: {strategy}")
                    job_found = True
                    break
                except:
                    continue
            
            # Additional wait for dynamic content
            if not job_found:
                logger.warning("Selenium: No job elements found with common selectors, waiting additional time...")
                time.sleep(5)  # Extra wait for slow-loading content
            
            # Get the fully rendered HTML
            html = driver.page_source
            logger.debug(f"Selenium got HTML of length: {len(html)}")
            
            # Debug: Log page title and URL to verify we're on the right page
            try:
                page_title = driver.title
                current_url = driver.current_url
                logger.info(f"Selenium page title: {page_title}")
                logger.info(f"Selenium current URL: {current_url}")
            except:
                pass
            
            # Try to find any job-related elements using various strategies
            logger.info("Selenium: Attempting to find job elements...")
            
            # Strategy 1: Try to find clickable job cards/elements
            try:
                clickable_jobs = driver.find_elements(By.XPATH, 
                    "//div[contains(@class, 'job') or contains(@class, 'position') or contains(@class, 'vacancy')]//a | " +
                    "//a[contains(@href, '/job/') or contains(@href, '/position/') or contains(@href, '/jobs/')]")
                logger.info(f"Selenium found {len(clickable_jobs)} clickable job elements")
            except:
                clickable_jobs = []
            
            # Strategy 2: Find all divs/articles that might contain jobs
            try:
                potential_jobs = driver.find_elements(By.XPATH,
                    "//div[contains(@class, 'card')] | //article | //section[contains(@class, 'job')] | " +
                    "//div[@role='article'] | //div[@role='listitem']")
                logger.info(f"Selenium found {len(potential_jobs)} potential job containers")
            except:
                potential_jobs = []
            
            # Save HTML for debugging
            try:
                debug_dir = os.path.join(settings.MEDIA_ROOT, 'scraper_debug')
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f"selenium_debug_{int(time.time())}.html")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info(f"Saved Selenium HTML debug file: {debug_file}")
            except Exception as e:
                logger.debug(f"Could not save Selenium debug HTML: {str(e)}")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract jobs from HTML - but prefer direct element extraction for better URL extraction
            jobs = []
            
            # Log page content for debugging
            page_text = driver.find_element(By.TAG_NAME, 'body').text[:500] if driver.find_elements(By.TAG_NAME, 'body') else ''
            logger.debug(f"Page text preview (first 500 chars): {page_text}")
            
            # First try direct Selenium element extraction (more reliable for URLs)
            if clickable_jobs or potential_jobs:
                logger.info(f"Selenium: Trying direct element extraction from {len(clickable_jobs)} links and {len(potential_jobs)} containers for search: '{keyword}' in '{location}'")
                for link in clickable_jobs[:15]:
                    try:
                        url = link.get_attribute('href') or ''
                        if not url or url == '#' or 'javascript:' in url.lower():
                            continue
                        
                        # Get parent container
                        try:
                            parent = link.find_element(By.XPATH, "./ancestor::div[1] | ./ancestor::article[1] | ./parent::*[1]")
                        except:
                            parent = link
                        
                        job_data = self._extract_job_data_from_element(parent, link)
                        if job_data and job_data.get('title'):
                            # Verify job matches search criteria (at least partially)
                            job_title = job_data.get('title', '').lower()
                            job_location = job_data.get('location', '').lower()
                            
                            # Check if job is relevant to search
                            keyword_matches = any(word in job_title for word in keyword.split() if len(word) > 3)
                            location_matches = any(word in job_location for word in location.split() if len(word) > 2)
                            
                            if keyword_matches or location_matches or not keyword or not location:
                                jobs.append(job_data)
                                logger.debug(f"Selenium extracted job: {job_data.get('title')} at {job_data.get('location')}")
                    except Exception as e:
                        logger.debug(f"Error extracting from link: {str(e)}")
                        continue
            
            # If HTML extraction is still needed, use it
            if len(jobs) == 0:
                jobs = self._extract_jobs(soup, keyword)
                logger.info(f"Selenium extracted {len(jobs)} jobs from HTML parsing for '{keyword}' in '{location}'")
            
            # If still no jobs, try extracting from Selenium WebElements directly
            if len(jobs) == 0:
                logger.warning("Selenium: No jobs from HTML extraction, trying direct element extraction...")
                
                # Try extracting from clickable job links
                for link in clickable_jobs[:15]:
                    try:
                        url = link.get_attribute('href') or ''
                        if not url or url == '#' or 'javascript:' in url:
                            continue
                        
                        # Get parent container
                        parent = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job') or contains(@class, 'card') or contains(@class, 'item')][1] | ./ancestor::article[1] | ./parent::*[1]")
                        
                        job_data = self._extract_job_data_from_element(parent, link)
                        if job_data and job_data.get('title'):
                            jobs.append(job_data)
                            logger.debug(f"Selenium extracted job from link: {job_data.get('title')}")
                    except Exception as e:
                        logger.debug(f"Error extracting from link: {str(e)}")
                        continue
                
                # Try extracting from potential job containers
                if len(jobs) == 0:
                    for container in potential_jobs[:15]:
                        try:
                            # Check if this container has job-like content
                            text = container.text.strip()
                            if len(text) > 20 and ('job' in text.lower() or 'position' in text.lower() or 'hiring' in text.lower()):
                                job_data = self._extract_job_data_from_element(container, None)
                                if job_data and job_data.get('title'):
                                    jobs.append(job_data)
                                    logger.debug(f"Selenium extracted job from container: {job_data.get('title')}")
                        except Exception as e:
                            logger.debug(f"Error extracting from container: {str(e)}")
                            continue
            
            logger.info(f"Selenium total jobs found: {len(jobs)}")

            return {
                'success': True,
                'jobs': jobs,
                'total_found': len(jobs),
                'keyword': keyword,
                'location': location,
                'message': f"Found {len(jobs)} job(s) for '{keyword}' in '{location}' via Selenium",
                'debug_info': {
                    'url_accessed': url,
                    'response_status': 200,
                    'note': 'Fetched with Selenium WebDriver',
                }
            }
        except Exception as sel_err:
            logger.error(f"Selenium fetch failed: {sel_err}")
            return None
        finally:
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass

    def _extract_job_data_from_element(self, parent_element, link_element=None) -> Optional[Dict]:
        """Extract job data from a Selenium WebElement"""
        try:
            from selenium.webdriver.common.by import By
            from urllib.parse import urljoin
            
            title = ''
            company = ''
            location = ''
            description = ''
            salary = ''
            url = ''
            
            # Try to get title from link or nearby elements
            if link_element:
                try:
                    title = link_element.text.strip()
                    url = link_element.get_attribute('href') or ''
                    # Try data attributes
                    if not url:
                        url = link_element.get_attribute('data-href') or ''
                    if not url:
                        url = link_element.get_attribute('data-url') or ''
                except:
                    pass
            
            # Try to find title in parent - try multiple selectors
            if not title:
                title_selectors = [
                    'h1', 'h2', 'h3', 'h4', 'h5',
                    '[class*="title"]', '[class*="Title"]',
                    '[class*="name"]', '[class*="Name"]',
                    'a[href*="job"]', 'a[href*="position"]',
                    'span[class*="title"]', 'div[class*="title"]'
                ]
                for selector in title_selectors:
                    try:
                        title_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                        title = title_elem.text.strip()
                        if title and len(title) > 3:
                            break
                    except:
                        continue
            
            # If still no title, try getting first meaningful text
            if not title:
                try:
                    all_text = parent_element.text.strip().split('\n')
                    for text in all_text:
                        if len(text) > 10 and len(text) < 200:
                            title = text.strip()
                            break
                except:
                    pass
            
            # Try to find URL - multiple strategies
            if not url or url == '#':
                # Look for any links in the parent
                try:
                    links = parent_element.find_elements(By.CSS_SELECTOR, 'a[href]')
                    for link in links:
                        href = link.get_attribute('href') or ''
                        if href and ('/job/' in href or '/position/' in href or '/jobs/' in href):
                            url = href
                            break
                except:
                    pass
            
            # Try data attributes for URL
            if not url or url == '#':
                try:
                    url = parent_element.get_attribute('data-href') or ''
                    if not url:
                        url = parent_element.get_attribute('data-url') or ''
                    if not url:
                        url = parent_element.get_attribute('data-link') or ''
                    if url and not url.startswith('http'):
                        url = urljoin(self.base_url, url)
                except:
                    pass
            
            # Construct URL from job ID if found
            if not url or url == '#':
                try:
                    job_id = parent_element.get_attribute('data-job-id') or ''
                    if not job_id:
                        job_id = parent_element.get_attribute('data-position-id') or ''
                    if job_id:
                        url = f"{self.base_url}/job/{job_id}"
                except:
                    pass
            
            # Fallback: use search page URL
            if not url or url == '#' or url == '':
                url = f"{self.base_url}/en-us/jobs-hiring"
            
            # Try to find company - multiple strategies
            company_selectors = [
                '[class*="company"]', '[class*="employer"]', '[class*="recruiter"]',
                '[class*="Organization"]', '[class*="Company"]',
                'span[class*="company"]', 'div[class*="company"]', 'p[class*="company"]'
            ]
            for selector in company_selectors:
                try:
                    company_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                    company = company_elem.text.strip()
                    if company and len(company) > 1:
                        break
                except:
                    continue
            
            # Try to find location - multiple strategies
            location_selectors = [
                '[class*="location"]', '[class*="address"]', '[class*="Location"]',
                '[class*="city"]', '[class*="region"]', '[class*="area"]',
                'span[class*="location"]', 'div[class*="location"]'
            ]
            for selector in location_selectors:
                try:
                    location_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                    location = location_elem.text.strip()
                    if location and len(location) > 1:
                        break
                except:
                    continue
            
            # Try to find salary
            salary_selectors = [
                '[class*="salary"]', '[class*="wage"]', '[class*="pay"]',
                '[class*="compensation"]', '[class*="Salary"]'
            ]
            for selector in salary_selectors:
                try:
                    salary_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                    salary = salary_elem.text.strip()
                    if salary:
                        break
                except:
                    continue
            
            # Get description from parent
            try:
                desc_elem = parent_element.find_element(By.CSS_SELECTOR, '[class*="description"], [class*="summary"], p[class*="desc"]')
                description = desc_elem.text.strip()
            except:
                # Get all text and use first few sentences
                try:
                    all_text = parent_element.text.strip()
                    # Take first 200 chars as description
                    description = all_text[:200] if len(all_text) > 200 else all_text
                except:
                    description = ''
            
            # Clean up the data
            title = title.strip() if title else ''
            company = company.strip() if company else ''
            location = location.strip() if location else ''
            
            if title and len(title) > 3:
                return {
                    'title': title,
                    'company': company or 'Company Not Specified',
                    'location': location or 'Location Not Specified',
                    'description': description or 'No description available',
                    'salary': salary or 'Salary not disclosed',
                    'url': url if url and url != '#' else f"{self.base_url}/en-us/jobs-hiring"
                }
        except Exception as e:
            logger.debug(f"Error extracting job data from Selenium element: {str(e)}")
        
        return None
    
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
        
        # If no valid URL found, try to find onclick handlers or data attributes on parent elements
        try:
            # Check parent element for data attributes
            parent = job_element.find_parent(['div', 'article', 'section'])
            if parent:
                data_job_id = parent.get('data-job-id') or parent.get('data-position-id') or parent.get('data-id')
                if data_job_id:
                    possible_url = f"{self.base_url}/job/{data_job_id}"
                    logger.debug(f"Found job ID from parent: {data_job_id}, constructed URL: {possible_url}")
                    return possible_url
                
                # Check for onclick handlers that might contain URLs
                onclick = parent.get('onclick', '')
                if onclick:
                    import re
                    url_match = re.search(r'/job/\d+|/position/\d+|/jobs/\d+', onclick)
                    if url_match:
                        url = f"{self.base_url}{url_match.group()}"
                        logger.debug(f"Extracted URL from onclick: {url}")
                        return url
        except:
            pass
        
        # Log at debug level instead of warning to reduce noise
        if debug_info:
            logger.debug(f"No valid job URL found. Debug info: {'; '.join(debug_info[:3])}")  # Limit debug info
        
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
    


# Singleton instance for BossJobScraper (for backward compatibility)
scraper = BossJobScraper()

# Multi-source scraper manager (optional import to avoid circular dependency)
try:
    from .scraper_manager import JobScraperManager
    scraper_manager = JobScraperManager()
except ImportError:
    scraper_manager = None
    logger.warning("JobScraperManager not available")