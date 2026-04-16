"""
Management command to scrape jobs from top Philippine job sites using botasaurus.

Usage:
    python manage.py scrape_ph_jobs --keyword "software engineer" --location "Manila"
    python manage.py scrape_ph_jobs --keyword "nurse" --location "Cebu" --sources JOBSTREET INDEED
    python manage.py scrape_ph_jobs --keyword "accountant" --location "Philippines" --save
    python manage.py scrape_ph_jobs --list-sources
"""
import json
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from jobs.botasaurus_scrapers.orchestrator import SCRAPERS, aggregate_jobs, scrape_all_sites

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Scrape job listings from top Philippine job sites using botasaurus."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keyword",
            type=str,
            default="",
            help="Job search keyword (e.g. 'software engineer')",
        )
        parser.add_argument(
            "--location",
            type=str,
            default="Philippines",
            help="Location to search in (default: Philippines)",
        )
        parser.add_argument(
            "--sources",
            nargs="+",
            choices=list(SCRAPERS.keys()),
            default=None,
            help="Limit scraping to specific sources. Defaults to all 10 sites.",
        )
        parser.add_argument(
            "--save",
            action="store_true",
            default=False,
            help="Save results to the ScrapedJob model in the database.",
        )
        parser.add_argument(
            "--user",
            type=str,
            default=None,
            help="Username to associate with saved ScrapedJob records (required with --save).",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=4,
            help="Number of parallel scraper threads (default: 4).",
        )
        parser.add_argument(
            "--list-sources",
            action="store_true",
            default=False,
            help="List all available source keys and exit.",
        )
        parser.add_argument(
            "--output-json",
            type=str,
            default=None,
            help="Optional path to write aggregated results as JSON.",
        )

    def handle(self, *args, **options):
        if options["list_sources"]:
            self.stdout.write(self.style.SUCCESS("Available sources:"))
            for key, (name, _) in SCRAPERS.items():
                self.stdout.write(f"  {key:<12} → {name}")
            return

        keyword = options["keyword"].strip()
        location = options["location"].strip()

        if not keyword:
            raise CommandError("--keyword is required. Use --list-sources to see available sources.")

        sources = options["sources"]
        workers = options["workers"]
        save = options["save"]
        username = options["user"]
        output_json = options["output_json"]

        # Resolve user for DB save
        user = None
        if save:
            if not username:
                # Fall back to first superuser
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    raise CommandError(
                        "--user is required when using --save (no superuser found as fallback)."
                    )
                self.stdout.write(
                    self.style.WARNING(f"No --user provided; using superuser '{user.username}'.")
                )
            else:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    raise CommandError(f"User '{username}' not found.")

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\nScraping '{keyword}' in '{location}' "
                f"from {len(sources or SCRAPERS)} site(s) with {workers} worker(s)...\n"
            )
        )

        results = scrape_all_sites(keyword, location, sources=sources, max_workers=workers)

        # ── Summary ──────────────────────────────────────────────────────────
        total_jobs = 0
        for result in results:
            src = result.get("source", "?")
            display_name = SCRAPERS.get(src, (src,))[0]
            count = result.get("total_found", 0)
            total_jobs += count

            if result.get("success"):
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {display_name:<30} {count} job(s)")
                )
            else:
                err = result.get("error", "unknown error")
                self.stdout.write(
                    self.style.WARNING(f"  ✗ {display_name:<30} FAILED — {err}")
                )

        self.stdout.write(f"\nTotal jobs scraped: {total_jobs}")

        # ── Save to DB ────────────────────────────────────────────────────────
        if save and user:
            from jobs.models import ScrapedJob

            saved = 0
            for result in results:
                if not result.get("jobs"):
                    continue
                src = result.get("source", "OTHER")
                ScrapedJob.objects.create(
                    search_keyword=keyword,
                    search_location=location,
                    source=src,
                    scraped_data=result,
                    total_found=result.get("total_found", 0),
                    scraped_by=user,
                )
                saved += 1

            self.stdout.write(
                self.style.SUCCESS(f"Saved {saved} ScrapedJob record(s) to the database.")
            )

        # ── JSON output ───────────────────────────────────────────────────────
        if output_json:
            all_jobs = aggregate_jobs(results)
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Wrote {len(all_jobs)} deduplicated job(s) to '{output_json}'."
                )
            )
