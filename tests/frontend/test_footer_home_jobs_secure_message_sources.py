"""Focused source and design regression guards; no Django dependency."""
import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding='utf-8')


class PageAndAttachmentRegressions(unittest.TestCase):
    def test_public_footer_is_scoped_without_inline_styles(self):
        footer = source('templates/components/footer.html')
        self.assertNotIn('<style>', footer)
        self.assertIn('site_config.facebook_url or', footer)
        self.assertIn('page.get_absolute_url', footer)
        self.assertIn('public-landing .landing-footer', source('static/css/footer.css'))

    def test_authenticated_footer_is_not_public_four_column_footer(self):
        self.assertIn("components/footer_authenticated.html", source('templates/base_alumni.html'))
        compact = source('templates/components/footer_authenticated.html')
        self.assertIn('Office of Alumni Affairs', compact)
        self.assertIn('page.get_absolute_url', compact)
        self.assertNotIn('contact-info', compact)

    def test_public_home_cms_and_sections_not_removed(self):
        home = source('templates/home.html')
        for expected in ['hero_headline', 'hero_subheadline', 'site_config.hero_background_image',
                         'upcoming_events', 'vmgo_section', 'staff_members', 'feedback_form',
                         'csrf_token', 'home-hero-secondary']:
            self.assertIn(expected, home)

    def test_public_job_detail_selects_public_shell(self):
        self.assertIn("'base_landingpage.html' if not request.user.is_authenticated", source('jobs/views.py'))
        self.assertIn("extends job_detail_page_base", source('jobs/templates/jobs/job_detail.html'))

    def test_chat_attachments_never_expose_media_storage_urls(self):
        templates = list((ROOT / 'templates/connections').rglob('*.html'))
        for template in templates:
            with self.subTest(template=template):
                self.assertNotIn('message.attachment.url', template.read_text(encoding='utf-8'))
        common = source('templates/connections/partials/message_attachment.html')
        self.assertIn('attachment_access_url', common)
        self.assertIn('attachment_label', common)
        self.assertNotIn('attachment.name', common)
        self.assertIn('participants.filter(pk=request.user.pk)', source('connections/views.py'))
        self.assertIn('PRIVATE_MESSAGE_UPLOAD_ROOT', source('connections/private_storage.py'))
        self.assertIn('block_legacy_message_media', source('norsu_alumni/urls.py'))


if __name__ == '__main__':
    unittest.main()
