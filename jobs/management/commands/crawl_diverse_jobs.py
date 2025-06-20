"""
Management command to crawl and import job postings from multiple categories.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from jobs.crawler.manager import CrawlerManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Crawl and import job postings from multiple categories and sources'
    
    # Define job categories covering diverse fields
    JOB_CATEGORIES = {
        'technology': [
            'software developer', 'web developer', 'data analyst', 'IT support',
            'cybersecurity', 'network engineer', 'system administrator'
        ],
        'finance': [
            'accountant', 'financial analyst', 'bookkeeper', 'finance manager',
            'auditor', 'tax specialist', 'banking'
        ],
        'healthcare': [
            'nurse', 'doctor', 'medical assistant', 'healthcare administrator',
            'physical therapist', 'pharmacist', 'caregiver'
        ],
        'education': [
            'teacher', 'professor', 'tutor', 'school administrator',
            'education coordinator', 'curriculum developer'
        ],
        'sales_marketing': [
            'sales representative', 'marketing specialist', 'digital marketer',
            'social media manager', 'brand manager', 'public relations'
        ],
        'hospitality': [
            'hotel manager', 'chef', 'restaurant staff', 'event coordinator',
            'customer service', 'tourism', 'hospitality'
        ],
        'manufacturing': [
            'production worker', 'plant manager', 'quality control',
            'warehouse supervisor', 'logistics coordinator', 'supply chain'
        ],
        'administrative': [
            'administrative assistant', 'office manager', 'receptionist',
            'executive assistant', 'data entry', 'clerical'
        ],
        'construction': [
            'construction worker', 'project manager', 'civil engineer',
            'architect', 'electrician', 'plumber', 'carpenter'
        ],
        'creative': [
            'graphic designer', 'content writer', 'photographer', 'videographer',
            'creative director', 'artist', 'animator'
        ]
    }
    
    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument('source', type=str, help='Job source to crawl (e.g., indeed, bossjobs)')
        
        # Optional arguments
        parser.add_argument('--location', type=str, default="", 
                          help='Location to search in (e.g., "San Francisco, CA")')
        parser.add_argument('--category', type=str, 
                          help='Specific category to crawl (default: all categories)')
        parser.add_argument('--max-jobs-per-category', type=int, default=10, 
                          help='Maximum number of jobs to crawl per category (default: 10)')
        parser.add_argument('--job-type', type=str, 
                          help='Filter by job type (e.g., fulltime, parttime)')
        parser.add_argument('--dry-run', action='store_true', 
                          help='Do not save jobs to database')
    
    def handle(self, *args, **options):
        source = options['source'].lower()
        location = options['location']
        category = options['category']
        max_jobs_per_category = options['max_jobs_per_category']
        job_type = options['job_type']
        dry_run = options['dry_run']
        
        # Initialize crawler manager
        manager = CrawlerManager()
        
        # Check if the source is supported
        available_sources = manager.list_available_sources()
        if source not in available_sources:
            raise CommandError(f"Unsupported job source: {source}. Available sources: {', '.join(available_sources)}")
        
        # Log command information
        self.stdout.write(self.style.NOTICE(f"Starting diverse job crawl from {source} at {timezone.now()}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: Jobs will not be saved to database"))
        
        total_jobs_found = 0
        total_jobs_created = 0
        total_jobs_updated = 0
        
        # Process categories
        categories_to_process = {}
        if category:
            # Process only the specified category
            if category.lower() in self.JOB_CATEGORIES:
                categories_to_process[category.lower()] = self.JOB_CATEGORIES[category.lower()]
            else:
                available_categories = list(self.JOB_CATEGORIES.keys())
                raise CommandError(f"Unsupported category: {category}. Available categories: {', '.join(available_categories)}")
        else:
            # Process all categories
            categories_to_process = self.JOB_CATEGORIES
        
        # Crawl jobs for each category
        for category_name, search_terms in categories_to_process.items():
            self.stdout.write(f"\nProcessing category: {category_name}")
            
            category_jobs_found = 0
            category_jobs_created = 0
            category_jobs_updated = 0
            
            for search_term in search_terms:
                self.stdout.write(f"  Searching for '{search_term}' jobs in '{location}'...")
                
                try:
                    # Search for jobs
                    search_kwargs = {
                        'max_jobs': max_jobs_per_category
                    }
                    
                    # Pass job type in kwargs if specified
                    if job_type:
                        search_kwargs['job_type'] = job_type
                    
                    # Call the manager with appropriate parameters
                    # Category is used in search_jobs, but should not be passed to crawler constructor
                    results = manager.search_and_save_jobs(
                        source=source,
                        query=search_term,
                        location=location,
                        save_to_db=not dry_run,
                        category=category_name,  # Pass category as a separate parameter
                        **search_kwargs
                    )
                    
                    # Count results
                    jobs_found = len(results)
                    jobs_created = sum(1 for r in results if r.get('created', False))
                    jobs_updated = jobs_found - jobs_created
                    
                    # Add to totals
                    category_jobs_found += jobs_found
                    category_jobs_created += jobs_created
                    category_jobs_updated += jobs_updated
                    
                    self.stdout.write(f"    Found {jobs_found} jobs ({jobs_created} created, {jobs_updated} updated)")
                    
                except Exception as e:
                    logger.exception(f"Error during job crawl for '{search_term}'")
                    self.stdout.write(self.style.ERROR(f"    Error: {str(e)}"))
            
            # Add to overall totals
            total_jobs_found += category_jobs_found
            total_jobs_created += category_jobs_created
            total_jobs_updated += category_jobs_updated
            
            # Category summary
            self.stdout.write(self.style.SUCCESS(
                f"  Category {category_name}: {category_jobs_found} jobs "
                f"({category_jobs_created} created, {category_jobs_updated} updated)"
            ))
        
        # Overall summary
        self.stdout.write("\n" + "="*40)
        self.stdout.write(self.style.SUCCESS(
            f"Overall crawl results: {total_jobs_found} jobs "
            f"({total_jobs_created} created, {total_jobs_updated} updated)"
        )) 