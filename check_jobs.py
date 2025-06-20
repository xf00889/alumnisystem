import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

# Import models
from jobs.models import JobPosting

# Count jobs
total_jobs = JobPosting.objects.count()
bossjobs_jobs = JobPosting.objects.filter(source="bossjobs").count()
indeed_jobs = JobPosting.objects.filter(source="indeed").count()

# Print counts
print(f"Total jobs in database: {total_jobs}")
print(f"BossJobs jobs: {bossjobs_jobs}")
print(f"Indeed jobs: {indeed_jobs}")

# Show recent BossJobs jobs
print("\nRecent BossJobs jobs:")
for job in JobPosting.objects.filter(source="bossjobs").order_by('-last_scraped')[:5]:
    print(f"{job.job_title} at {job.company_name}")

# Show unique BossJobs job titles
print("\nUnique BossJobs job titles:")
titles = JobPosting.objects.filter(source="bossjobs").values_list('job_title', flat=True).distinct()
for title in titles:
    print(f"- {title}") 