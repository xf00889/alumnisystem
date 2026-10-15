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
        self.assertIn('body.public-landing .landing-footer', source('static/css/public_redesign.css'))

    def test_authenticated_footer_is_not_public_four_column_footer(self):
        self.assertIn("components/footer_authenticated.html", source('templates/base_alumni.html'))
        compact = source('templates/components/footer_authenticated.html')
        self.assertIn('Office of Alumni Affairs', compact)
        self.assertNotIn('page.get_absolute_url', compact)
        self.assertNotIn('authenticated-footer-legal', compact)
        self.assertNotIn('contact-info', compact)
        footer_css = source('static/css/alumni/authenticated-footer.css')
        self.assertIn('white-space: nowrap', footer_css)
        self.assertIn('.authenticated-footer-institution { display: none; }', footer_css)

    def test_public_home_cms_and_sections_not_removed(self):
        home = source('templates/home.html')
        for expected in ['hero_headline', 'hero_subheadline', 'site_config.hero_background_image',
                         'upcoming_events', 'vmgo_section', 'staff_members', 'feedback_form',
                         'csrf_token', 'home-hero-secondary']:
            self.assertIn(expected, home)

    def test_all_public_job_data_routes_require_membership(self):
        jobs = source('jobs/views.py')
        for handler in ('job_list', 'careers', 'job_detail', 'get_job_details', 'check_job_application_eligibility'):
            self.assertIn('@job_board_login_required\ndef ' + handler + '(request', jobs)
        access = source('jobs/access.py')
        self.assertIn("redirect('core:home')", access)
        self.assertIn("extends alumni_page_base", source('jobs/templates/jobs/job_detail.html'))
        self.assertNotIn("'jobs': JobSitemap", source('norsu_alumni/urls.py'))

    def test_public_footer_spacing_has_one_override_owner(self):
        footer_style = source('static/css/footer.css')
        public_style = source('static/css/public_redesign.css')
        self.assertNotIn('/* NORSU public landing footer: remove inactive', footer_style)
        self.assertIn('grid-template-columns: repeat(auto-fit', public_style)
        self.assertNotIn('padding: clamp(4rem, 7vw, 6.5rem) 0 clamp(3rem, 5vw, 4.5rem)', public_style)

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
