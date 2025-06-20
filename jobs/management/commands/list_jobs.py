import logging
from django.core.management.base import BaseCommand
from django.db.models import Q
from jobs.models import JobPosting

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'List job postings from the database'

    def add_arguments(self, parser):
        parser.add_argument('source', type=str, nargs='?', default=None,
                          help='Filter by job source (e.g., indeed, bossjobs)')
        parser.add_argument('--limit', type=int, default=5,
                          help='Maximum number of jobs to display (default: 5)')
        parser.add_argument('--query', type=str, default=None,
                          help='Filter by search query used to find the job')
        parser.add_argument('--location', type=str, default=None,
                          help='Filter by search location used to find the job')
        parser.add_argument('--title', type=str, default=None,
                          help='Filter by job title (case-insensitive contains)')
        parser.add_argument('--company', type=str, default=None,
                          help='Filter by company name (case-insensitive contains)')
        parser.add_argument('--active-only', action='store_true',
                          help='Show only active job postings')
        parser.add_argument('--all', action='store_true',
                          help='Show all fields for each job')

    def handle(self, *args, **options):
        source = options['source']
        limit = options['limit']
        query = options['query']
        location = options['location']
        title_filter = options['title']
        company_filter = options['company']
        active_only = options['active_only']
        show_all = options['all']

        # Build filter conditions
        filters = Q()
        if source:
            filters &= Q(source=source.lower())
        if query:
            filters &= Q(search_query__icontains=query)
        if location:
            filters &= Q(search_location__icontains=location)
        if title_filter:
            filters &= Q(job_title__icontains=title_filter)
        if company_filter:
            filters &= Q(company_name__icontains=company_filter)
        if active_only:
            filters &= Q(is_active=True)

        # Get jobs
        jobs = JobPosting.objects.filter(filters).order_by('-last_scraped')[:limit]

        # Display results
        if source and query:
            self.stdout.write(f"Listing the latest {limit} jobs from {source} with query '{query}':")
        elif source:
            self.stdout.write(f"Listing the latest {limit} jobs from {source}:")
        else:
            self.stdout.write(f"Listing the latest {limit} jobs:")
            
        self.stdout.write("=" * 80)

        for job in jobs:
            self.stdout.write(f"Job ID: {job.id}")
            self.stdout.write(f"Title: {job.job_title}")
            self.stdout.write(f"Company: {job.company_name}")
            self.stdout.write(f"Location: {job.location}")
            self.stdout.write(f"Posted: {job.posted_date}")
            self.stdout.write(f"Last Scraped: {job.last_scraped}")
            self.stdout.write(f"URL: {job.application_link}")
            
            if show_all:
                self.stdout.write(f"Source: {job.source}")
                self.stdout.write(f"Source Type: {job.source_type}")
                self.stdout.write(f"Job Type: {job.job_type}")
                self.stdout.write(f"External ID: {job.external_id}")
                self.stdout.write(f"Search Query: {job.search_query}")
                self.stdout.write(f"Search Location: {job.search_location}")
                self.stdout.write(f"Category: {job.category}")
                self.stdout.write(f"Is Active: {job.is_active}")
                
            self.stdout.write("-" * 80)

        if not jobs:
            self.stdout.write("No jobs found matching the criteria.") 