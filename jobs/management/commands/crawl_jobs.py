"""
Management command to crawl and import job postings from external sources.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from jobs.crawler.manager import CrawlerManager

# Configure logging for this command
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to see all messages

class Command(BaseCommand):
    help = 'Crawl job listings from external sources'

    def add_arguments(self, parser):
        parser.add_argument('source', type=str, help='Job source (e.g., indeed, bossjobs)')
        parser.add_argument('query', type=str, help='Job search query')
        parser.add_argument('--location', type=str, default='Philippines',
                          help='Location to search in (default: Philippines)')
        parser.add_argument('--max-jobs', type=int, default=100,
                          help='Maximum number of jobs to fetch (default: 100)')
        parser.add_argument('--job-type', type=str,
                          help='Job type filter (e.g., fulltime, parttime)')
        parser.add_argument('--radius', type=int,
                          help='Search radius in miles/km')
        parser.add_argument('--days', type=int,
                          help='Jobs posted within this many days')
        parser.add_argument('--dry-run', action='store_true',
                          help='Do not save jobs to database, just display them')
        parser.add_argument('--refresh', action='store_true',
                          help='Refresh existing jobs instead of crawling new ones')
        parser.add_argument('--days-old', type=int, default=7,
                          help='Refresh jobs older than this many days (default: 7)')
        parser.add_argument('--category', type=str, 
                          help='Filter by job category (e.g., software, data science)')
    
    def handle(self, *args, **options):
        source = options['source']
        query = options['query']
        location = options['location']
        max_jobs = options['max_jobs']
        job_type = options['job_type']
        radius = options['radius']
        days = options['days']
        dry_run = options['dry_run']
        refresh = options['refresh']
        days_old = options['days_old']
        category = options['category']
        
        # Get current time for logging
        start_time = timezone.now()
        self.stdout.write(f"Starting job crawl from {source} at {start_time}")
        
        if dry_run:
            self.stdout.write("DRY RUN: Jobs will not be saved to database")
        
        # Initialize the crawler manager
        manager = CrawlerManager()
        
        # Check if the source is supported
        if source not in manager.list_available_sources():
            raise CommandError(f"Unsupported job source: {source}. Available sources: {', '.join(manager.list_available_sources())}")
        
        try:
            if refresh:
                # Refresh existing jobs
                self.stdout.write(f"Refreshing jobs from {source} older than {days_old} days...")
                refreshed_count = manager.refresh_jobs(source, days_old)
                self.stdout.write(f"Successfully refreshed {refreshed_count} jobs")
            else:
                # Search for jobs
                self.stdout.write(f"Searching for '{query}' jobs in '{location}' on {source} (max jobs: {max_jobs})...")
                
                # Set up search parameters
                search_kwargs = {
                    'max_jobs': max_jobs
                }
                
                if job_type:
                    search_kwargs['job_type'] = job_type
                if radius:
                    search_kwargs['radius'] = radius
                if days:
                    search_kwargs['days'] = days
                if category:
                    search_kwargs['category'] = category
                
                jobs = manager.search_and_save_jobs(
                    source=source,
                    query=query,
                    location=location,
                    save_to_db=not dry_run,
                    **search_kwargs
                )
                
                # Display results
                if dry_run:
                    self.stdout.write(f"Found {len(jobs)} jobs (not saved to database)")
                    self.stdout.write("Job Details:")
                    self.stdout.write("=" * 80)
                    
                    for i, job in enumerate(jobs, 1):
                        self.stdout.write(f"Job #{i}:")
                        self.stdout.write(f"Title: {job.get('job_title', 'N/A')}")
                        self.stdout.write(f"Company: {job.get('company_name', 'N/A')}")
                        self.stdout.write(f"URL: {job.get('application_link', 'N/A')}")
                        self.stdout.write(f"Search Query: {job.get('search_query', 'N/A')}")
                        self.stdout.write(f"Search Location: {job.get('search_location', 'N/A')}")
                        self.stdout.write("-" * 80)
                else:
                    created_count = sum(1 for job in jobs if job.get('created', False))
                    updated_count = len(jobs) - created_count
                    self.stdout.write(f"Successfully processed {len(jobs)} jobs ({created_count} created, {updated_count} updated)")
        except Exception as e:
            logger.exception("Error during job crawl")
            raise CommandError(f"Error during job crawl: {str(e)}") 