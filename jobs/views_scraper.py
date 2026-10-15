"""
Custom admin views for the multi-site job scraper.
Separate from Django admin - uses the custom admin dashboard.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction

from .models import ScrapedJob
from .botasaurus_scrapers.orchestrator import SCRAPERS, scrape_all_sites
from .admin_scraper_utils import publish_scraped_job

logger = logging.getLogger(__name__)


def is_hr_or_admin(user):
    """Check if user is HR, admin, or alumni coordinator"""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    try:
        return user.profile.is_hr or user.profile.is_alumni_coordinator
    except:
        return False


@login_required
@user_passes_test(is_hr_or_admin)
def scraper_dashboard(request):
    """
    Main scraper dashboard showing:
    - Form to trigger new scrape
    - List of recent scraped job records
    - Publish actions
    """
    from django import forms as django_forms

    class ScrapeForm(django_forms.Form):
        keyword = django_forms.CharField(
            max_length=100,
            label="Job keyword",
            widget=django_forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. software engineer, nurse, accountant",
                "autofocus": True,
            }),
        )
        location = django_forms.CharField(
            max_length=100,
            label="Location",
            initial="Philippines",
            widget=django_forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Manila, Cebu, Philippines",
            }),
        )
        sources = django_forms.MultipleChoiceField(
            choices=[(k, v[0]) for k, v in SCRAPERS.items()],
            initial=list(SCRAPERS.keys()),
            widget=django_forms.CheckboxSelectMultiple(attrs={
                "class": "form-check-input",
            }),
            label="Sites to scrape",
            required=True,
        )

    # Handle POST - run scraper
    if request.method == "POST" and "run_scraper" in request.POST:
        form = ScrapeForm(request.POST)
        if form.is_valid():
            keyword = form.cleaned_data["keyword"]
            location = form.cleaned_data["location"]
            sources = form.cleaned_data["sources"]

            messages.info(
                request,
                f"Scraping '{keyword}' in '{location}' from {len(sources)} site(s)… "
                "This may take up to 60 seconds.",
            )

            try:
                results = scrape_all_sites(keyword, location, sources=sources, max_workers=4)
            except Exception as exc:
                logger.error(f"Scraping failed: {exc}", exc_info=True)
                messages.error(request, f"Scraping failed: {exc}")
                return redirect("jobs:scraper_dashboard")

            saved = 0
            total_jobs = 0
            for result in results:
                if not result.get("jobs"):
                    continue
                src = result.get("source", "OTHER")
                # Deactivate previous entries for same search + source
                ScrapedJob.objects.filter(
                    search_keyword=keyword,
                    search_location=location,
                    source=src,
                    scraped_by=request.user,
                ).update(is_active=False)

                ScrapedJob.objects.create(
                    search_keyword=keyword,
                    search_location=location,
                    source=src,
                    scraped_data=result,
                    total_found=result.get("total_found", 0),
                    scraped_by=request.user,
                )
                saved += 1
                total_jobs += result.get("total_found", 0)

            messages.success(
                request,
                f"Done! Saved {saved} scrape record(s) with {total_jobs} total job(s). "
                "Use 'Publish' to make them visible to users.",
            )
            return redirect("jobs:scraper_dashboard")
    else:
        form = ScrapeForm()

    # Get recent scraped jobs
    recent_scrapes = ScrapedJob.objects.filter(
        scraped_by=request.user,
        is_active=True,
    ).order_by("-scraped_at")[:20]

    context = {
        "form": form,
        "recent_scrapes": recent_scrapes,
        "scrapers": SCRAPERS,
    }
    return render(request, "jobs/scraper_dashboard.html", context)


@login_required
@user_passes_test(is_hr_or_admin)
def publish_scraped_job_view(request, pk):
    """Publish a single ScrapedJob record to the job board."""
    try:
        scraped_job = ScrapedJob.objects.get(pk=pk, scraped_by=request.user)
    except ScrapedJob.DoesNotExist:
        messages.error(request, "Scraped job record not found.")
        return redirect("jobs:scraper_dashboard")

    summary = publish_scraped_job(scraped_job, posted_by=request.user)

    messages.success(
        request,
        f"Published {summary['published']} new job(s), "
        f"skipped {summary['skipped']} duplicate(s), "
        f"{summary['errors']} error(s).",
    )
    return redirect("jobs:scraper_dashboard")


@login_required
@user_passes_test(is_hr_or_admin)
def delete_scraped_job_view(request, pk):
    """Delete a ScrapedJob record."""
    try:
        scraped_job = ScrapedJob.objects.get(pk=pk, scraped_by=request.user)
        scraped_job.delete()
        messages.success(request, "Scraped job record deleted.")
    except ScrapedJob.DoesNotExist:
        messages.error(request, "Scraped job record not found.")
    return redirect("jobs:scraper_dashboard")
