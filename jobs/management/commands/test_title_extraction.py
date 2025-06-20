import logging
from django.core.management.base import BaseCommand
from jobs.crawler.bossjobs import BossJobsCrawler

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test the title extraction logic in the BossJobs crawler'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str,
                          help='Specific job URL to test')
        parser.add_argument('--max_jobs', type=int, default=3,
                          help='Maximum number of jobs to test')

    def handle(self, *args, **options):
        url = options['url']
        max_jobs = options['max_jobs']
        
        self.stdout.write(self.style.SUCCESS(f"Testing BossJobs title extraction logic"))
        
        crawler = BossJobsCrawler(delay=1.0, max_jobs=max_jobs)
        
        if url:
            self.test_specific_url(crawler, url)
        else:
            self.test_search_results(crawler, max_jobs)

    def test_search_results(self, crawler, max_jobs):
        self.stdout.write("Testing title extraction from search results...")
        
        jobs = crawler.search_jobs('software developer', 'Philippines')
        
        if not jobs:
            self.stdout.write(self.style.ERROR("No jobs found"))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Found {len(jobs)} jobs"))
        
        issue_count = 0
        for i, job in enumerate(jobs[:max_jobs]):
            self.stdout.write("\n" + "="*80)
            self.stdout.write(f"Job #{i+1}: {job.get('url', 'No URL')}")
            self.stdout.write("-"*80)
            
            title = job.get('title', 'Unknown Title')
            company = job.get('company', 'Unknown Company')
            
            self.stdout.write(f"Initial Title: '{title}'")
            self.stdout.write(f"Initial Company: '{company}'")
            
            # Get detailed job info
            self.stdout.write("\nFetching detailed info...")
            details = crawler.get_job_details(job['url'])
            
            detail_title = details.get('title', 'Unknown Title')
            detail_company = details.get('company', 'Unknown Company')
            
            self.stdout.write(f"Detailed Title: '{detail_title}'")
            self.stdout.write(f"Detailed Company: '{detail_company}'")
            
            # Check for issues
            if title.strip() == company.strip():
                self.stdout.write(self.style.ERROR("ISSUE: Search title equals company"))
                issue_count += 1
            else:
                self.stdout.write(self.style.SUCCESS("OK: Search title differs from company"))
                
            if detail_title.strip() == detail_company.strip():
                self.stdout.write(self.style.ERROR("ISSUE: Detailed title equals company"))
                issue_count += 1
            else:
                self.stdout.write(self.style.SUCCESS("OK: Detailed title differs from company"))
        
        self.stdout.write("\n" + "="*80)
        if issue_count > 0:
            self.stdout.write(self.style.ERROR(f"Found {issue_count} title issues"))
        else:
            self.stdout.write(self.style.SUCCESS("No title issues detected!"))

    def test_specific_url(self, crawler, url):
        self.stdout.write(f"Testing title extraction for specific URL: {url}")
        
        # Get detailed job info
        job_details = crawler.get_job_details(url)
        
        title = job_details.get('title', 'Unknown Title')
        company = job_details.get('company', 'Unknown Company')
        
        self.stdout.write(f"Title: '{title}'")
        self.stdout.write(f"Company: '{company}'")
        
        if title.strip() == company.strip():
            self.stdout.write(self.style.ERROR("ISSUE: Title equals company"))
        else:
            self.stdout.write(self.style.SUCCESS("OK: Title differs from company")) 