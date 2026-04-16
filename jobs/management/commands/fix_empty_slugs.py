"""
Fix JobPosting records that have empty or null slugs.
Run once after deploying the slug fix.

Usage:
    python manage.py fix_empty_slugs
"""
import re
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from jobs.models import JobPosting


class Command(BaseCommand):
    help = "Fix JobPosting records with empty or null slugs."

    def handle(self, *args, **options):
        broken = JobPosting.objects.filter(slug="") | JobPosting.objects.filter(slug__isnull=True)
        count = broken.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No broken slugs found."))
            return

        self.stdout.write(f"Found {count} job(s) with empty/null slugs. Fixing...")

        fixed = 0
        for job in broken:
            base_slug = slugify(f"{job.job_title}-{job.company_name}")
            if not base_slug:
                base_slug = f"job-{job.pk}"

            slug = base_slug
            n = 0
            while JobPosting.objects.filter(slug=slug).exclude(pk=job.pk).exists():
                n += 1
                clean = re.sub(r'-\d+$', '', base_slug)
                slug = f"{clean}-{n}"

            job.slug = slug
            job.save(update_fields=["slug"])
            fixed += 1
            self.stdout.write(f"  Fixed: '{job.job_title}' → slug='{slug}'")

        self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} slug(s)."))
