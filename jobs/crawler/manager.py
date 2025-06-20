"""
Job crawler manager that coordinates the crawling process and saving jobs to the database.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from ..models import JobPosting
from .base import BaseCrawler
from .indeed import IndeedCrawler
from .bossjobs import BossJobsCrawler

logger = logging.getLogger(__name__)

class CrawlerManager:
    """
    Manager for coordinating job crawlers and saving jobs to the database.
    """
    
    def __init__(self):
        """Initialize the crawler manager with available crawlers."""
        self.crawlers = {
            'indeed': IndeedCrawler,
            'bossjobs': BossJobsCrawler,
            # Add more crawlers as they are implemented
        }
    
    def get_crawler(self, source: str, **kwargs) -> Optional[BaseCrawler]:
        """
        Get a crawler instance for the specified source.
        
        Args:
            source: Name of the job source (e.g., 'indeed', 'linkedin')
            **kwargs: Additional parameters for the crawler
            
        Returns:
            BaseCrawler instance or None if the source is not supported
        """
        crawler_class = self.crawlers.get(source.lower())
        if crawler_class:
            return crawler_class(**kwargs)
        return None
    
    def list_available_sources(self) -> List[str]:
        """Return a list of available job sources."""
        return list(self.crawlers.keys())
    
    def search_and_save_jobs(self, source, query, location="", save_to_db=True, **kwargs):
        """
        Search for jobs using the specified crawler and save them to the database.
        
        Args:
            source: Job source (e.g., 'indeed', 'bossjobs')
            query: Job search query
            location: Location to search in
            save_to_db: Whether to save jobs to database
            **kwargs: Additional search parameters
            
        Returns:
            List of processed jobs
        """
        logger = logging.getLogger(__name__)
        
        # Separate crawler initialization parameters from search parameters
        crawler_kwargs = {
            'delay': kwargs.pop('delay', 1.0),
            'max_jobs': kwargs.pop('max_jobs', 100),
        }
        
        # Get the appropriate crawler
        crawler = self.get_crawler(source, **crawler_kwargs)
        
        if not crawler:
            logger.error(f"No crawler found for source: {source}")
            return []
            
        # Store the crawler for later use
        self.crawler = crawler
        
        # Search for jobs
        jobs = crawler.search_jobs(query, location, **kwargs)
        logger.info(f"Found {len(jobs)} jobs for query '{query}' in '{location}'")
        
        # Don't save to database if specified
        if not save_to_db:
            logger.info("Dry run - not saving jobs to database")
            return jobs
            
        # Process and save jobs
        processed_jobs = []
        for job in jobs:
            result = self.save_job_to_database(job, query, location)
            if result:
                job.update({
                    'created': result['created'],
                    'job_id': result['job'].id
                })
                processed_jobs.append(job)
        
        logger.info(f"Processed {len(processed_jobs)} jobs ({sum(1 for j in processed_jobs if j.get('created', False))} created, {len(processed_jobs) - sum(1 for j in processed_jobs if j.get('created', False))} updated)")
        return processed_jobs
    
    def refresh_jobs(self, source: str = None, days_old: int = 7) -> int:
        """
        Refresh jobs that are older than the specified number of days.
        
        Args:
            source: Name of the job source to refresh (None for all sources)
            days_old: Refresh jobs older than this many days
            
        Returns:
            Number of jobs refreshed
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        query = Q(last_scraped__lt=cutoff_date) | Q(last_scraped__isnull=True)
        
        if source:
            query &= Q(source=source.lower())
        
        jobs_to_refresh = JobPosting.objects.filter(
            query,
            source_type='EXTERNAL',  # Only refresh external jobs
            is_active=True  # Only refresh active jobs
        )
        
        refreshed_count = 0
        for job in jobs_to_refresh:
            try:
                crawler = self.get_crawler(job.source)
                if not crawler:
                    logger.warning(f"No crawler available for source: {job.source}")
                    continue
                
                # Get updated job details
                job_data = crawler.get_job_details(job.application_link)
                if not job_data:
                    logger.warning(f"Failed to refresh job: {job.job_title} at {job.company_name}")
                    continue
                
                # Standardize and update job
                standardized_job = crawler.standardize_job_data(job_data)
                
                # Update job fields
                job.job_title = standardized_job['job_title']
                job.company_name = standardized_job['company_name']
                job.location = standardized_job['location']
                job.job_description = standardized_job['job_description']
                job.requirements = standardized_job['requirements']
                job.responsibilities = standardized_job['responsibilities']
                job.skills_required = standardized_job['skills_required']
                job.salary_range = standardized_job['salary_range']
                job.job_type = standardized_job['job_type']
                job.last_scraped = timezone.now()
                
                # Check if job is still active
                if 'is_active' in job_data:
                    job.is_active = job_data['is_active']
                
                job.save()
                refreshed_count += 1
                logger.info(f"Refreshed job: {job.job_title} at {job.company_name}")
                
            except Exception as e:
                logger.error(f"Error refreshing job {job.id}: {str(e)}")
        
        logger.info(f"Refreshed {refreshed_count} jobs")
        return refreshed_count

    def save_job_to_database(self, job_data, query=None, location=None):
        """
        Save the job data to the database.
        
        Args:
            job_data: Dictionary containing job data
            query: The search query used to find this job
            location: The location search term
            
        Returns:
            A dictionary with the saved job object and a boolean indicating if it was created
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Print debug info
            logger.debug(f"Attempting to save job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            
            # Ensure we have the minimum required fields
            if not job_data.get('title') or not job_data.get('company'):
                logger.error(f"Missing required fields for job: {job_data}")
                return None
                
            # Get or create the job posting
            from jobs.models import JobPosting
            from django.utils.text import slugify
            import uuid
            
            # Standardize the job data
            standardized_data = self.crawler.standardize_job_data(job_data)
            
            # Debug log the standardized data
            logger.debug(f"Standardized job data: {standardized_data}")
            
            # Add the search query and location if provided
            if query:
                standardized_data['search_query'] = query
            if location:
                standardized_data['search_location'] = location
                
            # Generate a unique slug if not present
            if 'slug' not in standardized_data:
                # Create base slug from job title
                base_slug = slugify(standardized_data.get('job_title', 'job'))[:40]
                # Add company name to make it more unique
                company_slug = slugify(standardized_data.get('company_name', ''))[:20]
                # Create a unique identifier
                unique_id = str(uuid.uuid4())[:8]
                standardized_data['slug'] = f"{base_slug}-{company_slug}-{unique_id}"
            
            # Check if job already exists by source ID
            source = standardized_data.get('source')
            external_id = standardized_data.get('external_id')
            
            existing_job = None
            created = False
            
            if source and external_id:
                try:
                    existing_job = JobPosting.objects.get(source=source, external_id=external_id)
                    logger.debug(f"Found existing job with ID {existing_job.id}")
                except JobPosting.DoesNotExist:
                    logger.debug(f"No existing job found with source={source} and external_id={external_id}")
                    existing_job = None
            
            # If job exists, update it
            if existing_job:
                logger.debug(f"Updating existing job: {existing_job.job_title}")
                
                # Update fields
                for key, value in standardized_data.items():
                    if key != 'slug':  # Don't update slug
                        setattr(existing_job, key, value)
                
                existing_job.last_scraped = timezone.now()
                existing_job.save()
                logger.debug(f"Job updated successfully with ID {existing_job.id}")
                
                return {
                    'job': existing_job,
                    'created': False
                }
            else:
                # Create new job
                logger.debug(f"Creating new job: {standardized_data.get('job_title')}")
                
                # Set default values for required fields if not present
                if 'job_type' not in standardized_data:
                    standardized_data['job_type'] = 'FULLTIME'
                if 'source_type' not in standardized_data:
                    standardized_data['source_type'] = 'EXTERNAL'
                if 'is_active' not in standardized_data:
                    standardized_data['is_active'] = True
                
                # Set scrape timestamp
                standardized_data['last_scraped'] = timezone.now()
                
                # Create the job
                try:
                    job = JobPosting.objects.create(**standardized_data)
                    logger.debug(f"Job created successfully with ID {job.id}")
                    
                    return {
                        'job': job,
                        'created': True
                    }
                except Exception as e:
                    logger.error(f"Error creating job: {str(e)}")
                    logger.error(f"Problematic data: {standardized_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None 