"""Focused regression checks for member content cleanup and staff preview routing.

Only source-level tests here: run browser / HTTP permission acceptance separately.
"""
from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


class AlumniContentCleanupTests(SimpleTestCase):
    def test_member_event_modal_does_not_duplicate_title_metadata(self):
        modal = read('templates/events/event_detail_modal.html')
        self.assertIn('class="modal-event-title"', modal)
        self.assertNotIn('EVENT DETAILS', modal)
        self.assertNotIn('modal-status-badge', modal)
        self.assertIn('class="modal-rsvp-section"', modal)
        self.assertIn("{% url 'events:event_rsvp' event.pk %}", modal)
        self.assertIn('event.notified_groups.exists', modal)

    def test_member_announcement_list_is_card_only(self):
        template = read('templates/announcements/announcement_list.html')
        self.assertIn('id="announcementsGrid"', template)
        for removed in ('view-toggle-section', 'id="announcementsTable"',
                        'id="tableViewBtn"', 'switchView(', 'announcementsView'):
            self.assertNotIn(removed, template)
        self.assertIn("card.querySelector('.announcement-preview')", template)
        self.assertIn('id="announcementModal"', template)

    def test_full_width_survey_empty_state(self):
        template = read('templates/surveys/survey_list.html')
        css = read('static/css/alumni/surveys.css')
        self.assertIn('survey-empty-column', template)
        self.assertIn('No Active Surveys', template)
        self.assertIn('grid-column:1 / -1', css)
        self.assertIn('survey-empty-content', css)

    def test_campaign_breadcrumb_and_shared_spacing(self):
        detail = read('templates/donations/campaign_detail.html')
        breadcrumbs = read('templates/alumni/components/breadcrumbs.html')
        css = read('static/css/alumni/donations.css')
        self.assertIn("parent_area='Fundraising campaigns'", detail)
        self.assertIn("parent_url=fundraising_campaigns_url", detail)
        self.assertIn('parent_area and parent_url', breadcrumbs)
        self.assertIn('admin-donations-container{padding-top:0!important}', css)
        self.assertIn('fe-page--donations-campaign-list-html', read('templates/donations/campaign_list.html'))
        self.assertIn("area='Fundraising campaigns'", read('templates/donations/campaign_list.html'))

    def test_admin_announcement_is_modal_only_but_member_detail_remains(self):
        views = read('announcements/views.py')
        admin_template = read('templates/announcements/announcement_list_admin.html')
        preview = read('templates/announcements/partials/admin_announcement_preview.html')
        self.assertIn('return HttpResponseRedirect(', views)
        self.assertIn('preview={self.kwargs', views)
        self.assertIn("return super().get(request, *args, **kwargs)", views)
        self.assertIn('auto_preview_id', admin_template)
        self.assertIn('announcementAutoPreview', read('static/js/admin/content-management.js'))
        self.assertIn('Edit announcement', preview)
        self.assertNotIn('Open full page', preview)
        self.assertIn("name='announcement-detail'", read('announcements/urls.py'))

    def test_staff_preview_remains_permission_checked(self):
        views = read('announcements/views.py')
        self.assertIn("def admin_announcement_preview(request, pk):", views)
        self.assertIn("raise PermissionDenied('Announcement management permission required.')", views)
        self.assertIn("response['Cache-Control'] = 'private, no-store'", views)

    def test_cleanup_does_not_remove_alumni_sharing_and_filters(self):
        announcements = read('templates/announcements/announcement_list.html')
        self.assertIn('data-share-action="shareToFacebook"', announcements)
        self.assertIn('id="searchInput"', announcements)
        self.assertIn('data-filter="urgent"', announcements)
        self.assertIn('setupCheckboxes()', announcements)
