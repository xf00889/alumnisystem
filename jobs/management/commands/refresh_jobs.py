"""
Management command to refresh existing job postings in the database.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from jobs.crawler.manager import CrawlerManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh existing job postings from external sources'
    
    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument('--source', type=str, 
                          help='Specific job source to refresh (e.g., indeed)')
        parser.add_argument('--days-old', type=int, default=7,
                          help='Refresh jobs older than this many days (default: 7)')
        parser.add_argument('--limit', type=int,
                          help='Maximum number of jobs to refresh')
    
    def handle(self, *args, **options):
        source = options.get('source')
        days_old = options['days_old']
        
        # Initialize crawler manager
        manager = CrawlerManager()
        
        # Check if the source is supported (if specified)
        if source:
            available_sources = manager.list_available_sources()
            if source.lower() not in available_sources:
                raise CommandError(f"Unsupported job source: {source}. Available sources: {', '.join(available_sources)}")
        
        # Log command information
        start_time = timezone.now()
        self.stdout.write(self.style.NOTICE(f"Starting job refresh at {start_time}"))
        
        if source:
            self.stdout.write(f"Refreshing jobs from {source} older than {days_old} days...")
        else:
            self.stdout.write(f"Refreshing all external jobs older than {days_old} days...")
        
        try:
            # Refresh existing jobs
            refreshed_count = manager.refresh_jobs(source, days_old)
            
            end_time = timezone.now()
            duration = end_time - start_time
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully refreshed {refreshed_count} jobs in {duration.total_seconds():.2f} seconds"
            ))
                
        except Exception as e:
            logger.exception("Error during job refresh")
            raise CommandError(f"Job refresh failed: {str(e)}") 