"""Regression contract for independent content directories and compact alumni dialogs.

Source-focused checks: the corresponding live browser/permission workflows are
listed in the package QA matrix and must run on the deployment host.
"""
from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


def content(path):
    return (ROOT / path).read_text(encoding='utf-8')


class AdminContentRefinementTests(SimpleTestCase):
    def test_announcement_administration_is_independent_of_member_list(self):
        views = content('announcements/views.py')
        self.assertIn("return ['announcements/announcement_list_admin.html']", views)
        self.assertIn("def admin_announcement_preview(request, pk):", views)
        self.assertIn("raise PermissionDenied('Announcement management permission required.')", views)
        self.assertIn("response['Cache-Control'] = 'private, no-store'", views)
        admin = content('templates/announcements/announcement_list_admin.html')
        self.assertIn('data-modal-url=', admin)
        self.assertIn('Announcement Administration', admin)
        self.assertNotIn('announcements-grid', admin)
        self.assertIn("announcements:admin-announcement-preview", admin)

    def test_admin_event_and_campaign_modals_keep_protected_controls(self):
        for name, action in (
            ('templates/events/admin_event_detail_modal.html', 'events:event_update'),
            ('donations/templates/donations/partials/admin_campaign_preview.html', 'donations:campaign_edit'),
        ):
            self.assertIn(action, content(name))
        styles = content('static/css/admin/content-management.css')
        self.assertIn('.staff-content-modal[open]', styles)
        self.assertIn('.staff-content-preview dl>div{display:flex', styles)
        self.assertIn('.staff-content-preview>img{height:145px', styles)


class AlumniContentRefinementTests(SimpleTestCase):
    def test_events_are_card_only_and_rsvp_is_preserved(self):
        listing = content('templates/events/event_list_new.html')
        self.assertIn('class="events-grid"', listing)
        self.assertNotIn('id="eventsTable"', listing)
        self.assertNotIn('id="tableViewBtn"', listing)
        self.assertNotIn('eventsView', listing)
        self.assertIn(".event-preview')?.textContent", listing)
        self.assertIn('data-event-id=', listing)
        self.assertIn('id="eventModal"', listing)
        self.assertIn("{% url 'events:event_rsvp' event.pk %}",
                      content('templates/events/event_detail_modal.html'))

    def test_member_modals_have_one_close_control_and_social_actions(self):
        event_list = content('templates/events/event_list_new.html')
        announcement_list = content('templates/announcements/announcement_list.html')
        for listing in (event_list, announcement_list):
            self.assertIn('aria-label="Close', listing)
            self.assertNotIn('onclick="closeEventModal()">\n                    <i class="fas fa-times me-1', listing)
            self.assertNotIn('onclick="closeAnnouncementModal()">\n                        <i class="fas fa-times me-1', listing)
        self.assertIn('data-platform="facebook"', event_list)
        self.assertIn('data-share-action="shareToFacebook"', announcement_list)
        self.assertIn('metaHtml.trim() ?', announcement_list)

    def test_donor_breadcrumb_and_compact_campaign_image(self):
        donors = content('templates/donations/campaign_donors.html')
        detail = content('templates/donations/campaign_detail.html')
        self.assertIn("include 'alumni/components/breadcrumbs.html' with area='Campaign donors'", donors)
        self.assertIn('alumni-donors-panel', donors)
        self.assertIn('alumni-campaign-cover', detail)
        css = content('static/css/alumni/donations.css')
        self.assertIn('.alumni-campaign-cover{height:220px', css)
        self.assertIn('.alumni-donors-panel', css)

    def test_modal_styles_are_scoped_to_alumni_feature(self):
        for css_path, modal_id in (
            ('static/css/alumni/content-pages.css', '#eventModal'),
            ('static/css/alumni/announcements.css', '#announcementModal'),
        ):
            css = content(css_path)
            self.assertIn('body.alumni-portal .alumni-main[data-feature=', css)
            self.assertIn(modal_id, css)
