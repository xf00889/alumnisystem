from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from jobs.models import JobPosting
import requests
import json
from datetime import datetime
import time
from decouple import config

class Command(BaseCommand):
    help = 'Scrapes job postings from Indeed using Apify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keywords',
            type=str,
            help='Keywords to search for (e.g., "software engineer")',
            default='software developer,data analyst,project manager'
        )
        parser.add_argument(
            '--location',
            type=str,
            help='Location to search in',
            default='Philippines'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of jobs to scrape',
            default=50
        )

    def handle(self, *args, **options):
        APIFY_API_TOKEN = config('APIFY_API_TOKEN', default='')
        if not APIFY_API_TOKEN:
            self.stdout.write(self.style.ERROR('APIFY_API_TOKEN not found in environment variables'))
            return

        # Create a run configuration
        run_input = {
            "keyword": options['keywords'],
            "location": options['location'],
            "maxItems": options['limit'],
            "country": "ph",
            "maxConcurrency": 1,
            "extendOutputFunction": """($) => {
                return {
                    title: $('h1.jobsearch-JobInfoHeader-title').text().trim(),
                    company: $('.jobsearch-InlineCompanyRating').text().trim(),
                    location: $('.jobsearch-JobInfoHeader-subtitle').text().trim(),
                    description: $('#jobDescriptionText').text().trim(),
                    salary: $('.jobsearch-JobMetadataHeader-item').text().trim(),
                    url: window.location.href
                }
            }"""
        }

        # Start the actor run using the correct API endpoint
        self.stdout.write(f"Starting Indeed scraper for {options['keywords']} in {options['location']}")
        
        # Start the actor run
        response = requests.post(
            'https://api.apify.com/v2/acts/uraniumreza~indeed-jobs-scraper/runs',
            headers={
                'Authorization': f'Bearer {APIFY_API_TOKEN}',
                'Content-Type': 'application/json'
            },
            json=run_input
        )

        if response.status_code not in [201, 200]:
            self.stdout.write(self.style.ERROR(f'Failed to start the actor: {response.text}'))
            return

        run_data = response.json()
        run_id = run_data.get('data', {}).get('id')
        
        if not run_id:
            self.stdout.write(self.style.ERROR('Failed to get run ID from response'))
            return

        self.stdout.write(f"Actor run started with ID: {run_id}")

        # Wait for the run to finish
        while True:
            status_response = requests.get(
                f'https://api.apify.com/v2/actor-runs/{run_id}',
                headers={'Authorization': f'Bearer {APIFY_API_TOKEN}'}
            )
            
            if status_response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Failed to get run status: {status_response.text}'))
                return

            status = status_response.json().get('data', {}).get('status')
            if status == 'SUCCEEDED':
                break
            elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                self.stdout.write(self.style.ERROR(f'Actor run failed with status: {status}'))
                return
            
            time.sleep(10)  # Wait 10 seconds before checking again

        # Get the results from the dataset
        results_response = requests.get(
            f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
            headers={'Authorization': f'Bearer {APIFY_API_TOKEN}'}
        )

        if results_response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to get results: {results_response.text}'))
            return

        jobs = results_response.json()
        jobs_created = 0
        jobs_updated = 0

        for job in jobs:
            # Clean and prepare the data
            job_data = {
                'job_title': job.get('title', '')[:200],
                'company_name': job.get('company', '')[:200],
                'location': job.get('location', '')[:200],
                'job_description': job.get('description', ''),
                'application_link': job.get('url', ''),
                'external_id': job.get('id', str(hash(job.get('url', '')))),
                'source': 'indeed',
                'last_scraped': timezone.now(),
                'job_type': self._determine_job_type(job.get('title', '').lower()),
                'salary_range': job.get('salary', '')
            }

            # Update or create the job posting
            try:
                obj, created = JobPosting.objects.update_or_create(
                    external_id=job_data['external_id'],
                    source='indeed',
                    defaults=job_data
                )
                if created:
                    jobs_created += 1
                else:
                    jobs_updated += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error saving job: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {len(jobs)} jobs. '
            f'Created: {jobs_created}, Updated: {jobs_updated}'
        ))

    def _determine_job_type(self, title):
        """Helper method to determine job type based on title"""
        title = title.lower()
        if 'part time' in title or 'part-time' in title:
            return 'PART_TIME'
        elif 'contract' in title or 'contractor' in title:
            return 'CONTRACT'
        elif 'intern' in title or 'internship' in title:
            return 'INTERNSHIP'
        elif 'remote' in title:
            return 'REMOTE'
        return 'FULL_TIME' 