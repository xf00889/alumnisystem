"""Preview and, after approval, safely update the five known NORSU legal documents.

Only auto-replace pages still matching the official known seed text, optionally
followed by the unmodified October 2026 platform addendum. Never replace CMS
administrator changes automatically.
"""
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction

from cms.models import LegalPage
from cms.legal_plain_language import PLAIN_LANGUAGE_PAGES
from cms.management.commands.seed_legal_pages import DEFAULT_LEGAL_PAGES

KNOWN_DEFAULTS = {p['page_type']: p['content'].strip() for p in DEFAULT_LEGAL_PAGES}
try:
    from cms.management.commands.update_privacy_documents import ADDITIONS
except ImportError:
    ADDITIONS = {}


def is_known_draft(page_type, content):
    text = content.strip()
    default = KNOWN_DEFAULTS.get(page_type, '')
    addition = ADDITIONS.get(page_type, '').strip()
    return (text == default or
            bool(addition) and text == default + '\n\n---\n\n' + addition)


class Command(BaseCommand):
    help = 'Preview plain-language updates to all five legal pages; --apply requires NORSU legal approval.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Replace only unchanged known drafts after approval')

    def handle(self, *args, **opts):
        changed = skipped = 0
        for page_type, text in PLAIN_LANGUAGE_PAGES.items():
            try:
                page = LegalPage.objects.get(page_type=page_type)
            except LegalPage.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'{page_type}: MISSING; no change'))
                skipped += 1
                continue
            if page.content.strip() == text.strip():
                self.stdout.write(f'{page_type}: already uses plain language')
                continue
            if not is_known_draft(page_type, page.content):
                self.stdout.write(self.style.WARNING(
                    f'{page_type}: CUSTOMIZED or UNRECOGNIZED; do not overwrite. Review draft in cms/legal_plain_language.py via CMS editor.'))
                skipped += 1
                continue
            self.stdout.write(f'{page_type}: READY for reviewed plain-language replacement')
            if opts['apply']:
                with transaction.atomic():
                    locked = LegalPage.objects.select_for_update().get(pk=page.pk)
                    if not is_known_draft(page_type, locked.content):
                        self.stdout.write(self.style.WARNING(f'{page_type}: changed during review; skipped'))
                        skipped += 1
                        continue
                    locked.content = text.strip()
                    locked.effective_date = date(2026, 10, 18)
                    locked.save(update_fields=['content', 'effective_date', 'modified'])
                    changed += 1
        if not opts['apply']:
            self.stdout.write('DRY RUN ONLY. NORSU privacy/legal review required before --apply.')
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {changed} page(s); {skipped} skipped for manual review.'))
