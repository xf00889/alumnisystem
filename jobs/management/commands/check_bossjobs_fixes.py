from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
from bs4 import BeautifulSoup
import time
from jobs.models import JobPosting
from jobs.crawler.bossjobs import BossJobsCrawler
from urllib.parse import urljoin

class Command(BaseCommand):
    help = 'Check BossJobs crawler title fixes by comparing raw titles with saved titles'

    def add_arguments(self, parser):
        parser.add_argument('--max_jobs', type=int, default=5, 
                          help='Maximum number of jobs to check')
        parser.add_argument('--query', type=str, default='software developer',
                          help='Query to use for job search')

    def handle(self, *args, **options):
        max_jobs = options['max_jobs']
        query = options['query']
        location = "Philippines"  # Default location
        
        self.stdout.write(self.style.SUCCESS(f"Checking BossJobs title fixes..."))
        self.stdout.write(f"Query: {query}, Location: {location}")
        self.stdout.write("=" * 80)
        
        # Fetch raw HTML from BossJobs search page
        search_url = f"https://www.bossjob.ph/jobs/search?q={query}&l={location}"
        self.stdout.write(f"Fetching search page: {search_url}")
        
        try:
            response = requests.get(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml"
                },
                timeout=15
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards
            job_cards = []
            selectors = [
                'div.job-card', 'div.job-listing', 'div[data-job-id]',
                'div.job-post-card', 'div.job-search-card', 'div.job-item',
                'div[class*="job-card"]', 'div[class*="job-listing"]',
                'div.card', 'article.job', 'div.search-result-card'
            ]
            
            for selector in selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    self.stdout.write(f"Found {len(job_cards)} job cards with selector: {selector}")
                    break
                    
            if not job_cards:
                self.stdout.write(self.style.ERROR("No job cards found"))
                return
                
            # Process the first few job cards
            raw_jobs = []
            for idx, card in enumerate(job_cards[:max_jobs]):
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
                        
                    job_url = urljoin("https://www.bossjob.ph", job_link.get('href'))
                    
                    # Extract text directly from the card
                    raw_text = card.get_text(strip=True)
                    
                    # Find the text commonly found in job cards
                    link_text = job_link.get_text(strip=True) if job_link else "Unknown"
                    
                    # Find company name specifically
                    company_name = "Unknown"
                    company_selectors = [
                        'span.company-name', 'div.company-name', 'a.company-name',
                        '[class*="company-name"]', 'span.company', 'div.company'
                    ]
                    for selector in company_selectors:
                        company_elem = card.select_one(selector)
                        if company_elem:
                            company_name = company_elem.get_text(strip=True)
                            break
                            
                    raw_jobs.append({
                        'url': job_url,
                        'raw_text': raw_text[:100] + "...",
                        'link_text': link_text,
                        'company_name': company_name,
                        'same_text': link_text == company_name
                    })
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing card {idx}: {str(e)}"))
                    
            # Get saved job listings from the database
            db_jobs = JobPosting.objects.filter(
                source='bossjobs',
                search_query=query,
                last_scraped__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-last_scraped')
            
            if not db_jobs:
                self.stdout.write(self.style.ERROR("No saved jobs found in database for this query"))
                
            self.stdout.write(f"Found {len(raw_jobs)} raw job cards and {db_jobs.count()} saved jobs")
            self.stdout.write("")
            
            # Display raw data
            self.stdout.write(self.style.SUCCESS("Raw job card data:"))
            self.stdout.write("-" * 80)
            
            for i, job in enumerate(raw_jobs, 1):
                self.stdout.write(f"Job Card #{i}:")
                self.stdout.write(f"URL: {job['url']}")
                self.stdout.write(f"Raw Text Sample: {job['raw_text']}")
                self.stdout.write(f"Link Text: {job['link_text']}")
                self.stdout.write(f"Company Element Text: {job['company_name']}")
                
                if job['same_text']:
                    self.stdout.write(self.style.ERROR("❌ ISSUE DETECTED: Link text equals company name"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Link text differs from company name"))
                    
                # Try to find matching saved job
                matching_jobs = [j for j in db_jobs if job['url'] in j.application_link]
                
                if matching_jobs:
                    saved_job = matching_jobs[0]
                    self.stdout.write(f"DB Job Title: {saved_job.job_title}")
                    self.stdout.write(f"DB Company: {saved_job.company_name}")
                else:
                    self.stdout.write(self.style.WARNING("No matching saved job found"))
                    
                self.stdout.write("-" * 80)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching search page: {str(e)}")) 