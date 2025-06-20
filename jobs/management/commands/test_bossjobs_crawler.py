import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from jobs.crawler.bossjobs import BossJobsCrawler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test the BossJobs crawler and verify title extraction'

    def add_arguments(self, parser):
        parser.add_argument('query', type=str, help='Job search query')
        parser.add_argument('--location', type=str, default='Philippines', help='Location to search in')
        parser.add_argument('--max-jobs', type=int, default=5, help='Maximum number of jobs to fetch')

    def handle(self, *args, **options):
        query = options['query']
        location = options['location']
        max_jobs = options['max_jobs']
        
        self.stdout.write(f"Testing BossJobs crawler with query '{query}' in '{location}'")
        
        # Initialize the crawler
        crawler = BossJobsCrawler(max_jobs=max_jobs)
        
        # Search for jobs
        jobs = crawler.search_jobs(query, location)
        
        self.stdout.write(f"Found {len(jobs)} jobs")
        
        # Display job details
        for i, job in enumerate(jobs, 1):
            self.stdout.write("=" * 80)
            self.stdout.write(f"Job #{i}:")
            self.stdout.write(f"Title: {job.get('title', 'N/A')}")
            self.stdout.write(f"Company: {job.get('company', 'N/A')}")
            self.stdout.write(f"URL: {job.get('url', 'N/A')}")
            
            # Standardize job data
            standardized_job = crawler.standardize_job_data(job)
            
            self.stdout.write("\nStandardized Job Data:")
            self.stdout.write(f"Job Title: {standardized_job.get('job_title', 'N/A')}")
            self.stdout.write(f"Company Name: {standardized_job.get('company_name', 'N/A')}")
            self.stdout.write(f"External ID: {standardized_job.get('external_id', 'N/A')}")
            self.stdout.write(f"Source: {standardized_job.get('source', 'N/A')}")
            self.stdout.write("-" * 80) 