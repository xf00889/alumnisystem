"""Source-level regression checks for alumni/staff UI separation.

These run without requiring external email, media, or job scraping services.
For functional acceptance, also test the real views and forms on the VPS.
"""
from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding='utf-8')


class AlumniContentPageSeparationTests(SimpleTestCase):
    def test_campaign_staff_directory_and_preview_are_permission_checked(self):
        views = source('donations/views.py')
        self.assertIn("'donations/admin_campaign_directory.html'", views)
        self.assertIn("def admin_campaign_preview(request, pk):", views)
        self.assertIn('if not can_manage_donations(request.user):', views)
        self.assertIn('raise PermissionDenied', views)
        self.assertIn("'donations/partials/admin_campaign_preview.html'", views)

    def test_event_staff_view_is_not_alumni_template(self):
        views = source('events/views.py')
        self.assertIn("return ['events/event_list_admin.html']", views)
        self.assertIn("return ['events/admin_event_detail_modal.html']", views)
        self.assertIn("queryset = queryset.filter(status__in=['published', 'completed'])", views)

    def test_member_event_rsvp_is_preserved(self):
        self.assertIn("{% url 'events:event_rsvp' event.pk %}", source('templates/events/event_detail_modal.html'))
        self.assertIn('class="modal-rsvp-section"', source('templates/events/event_detail_modal.html'))
        self.assertIn('id="eventModal"', source('templates/events/event_list_new.html'))

    def test_announcements_preview_remains_plain_text_and_searchable(self):
        template = source('templates/announcements/announcement_list.html')
        self.assertIn('announcement-preview--plain', template)
        self.assertIn("announcement.content|striptags|truncatewords:20", template)
        self.assertIn("card.querySelector('.announcement-preview')", template)

    def test_regular_job_details_use_alumni_base(self):
        template = source('jobs/templates/jobs/job_detail.html')
        self.assertIn('extends alumni_page_base', template)
        self.assertIn('css/alumni/content-pages.css', template)
        for phrase in ('AI Match Score', 'Apply on External Site', 'shareJob()'):
            self.assertIn(phrase, template)

    def test_invalid_form_uploads_are_owner_bound(self):
        helper = source('core/pending_form_images.py')
        self.assertIn('max_age=3600', helper)
        self.assertIn("data.get('uid') != request.user.pk", helper)
        self.assertIn("not str(data.get('path', '')).startswith('pending-form-images/')", helper)
        self.assertIn('MAX_SIZE = 5 * 1024 * 1024', helper)
        self.assertIn("response['Cache-Control'] = 'private, no-store, max-age=0'", helper)

    def test_event_form_renders_saved_not_transient_filename(self):
        template = source('templates/events/event_form.html')
        self.assertIn('saved_event_image_url', template)
        self.assertIn('pending_image_token', template)
        self.assertNotIn('src="{{ form.instance.image.url }}"', template)

    def test_campaign_form_uses_confirmation_and_retained_upload(self):
        template = source('donations/templates/donations/campaign_form.html')
        self.assertIn('data-confirm-submit', template)
        self.assertIn('pending_image_token', template)
        self.assertIn('js/admin/content-management.js', template)

    def test_admin_modal_has_no_member_donation_form(self):
        preview = source('donations/templates/donations/partials/admin_campaign_preview.html')
        self.assertNotIn('DonationForm', preview)
        self.assertIn("donations:campaign_edit", preview)

    def test_alumni_card_previews_are_not_boxed(self):
        css = source('static/css/alumni/content-pages.css')
        self.assertIn('.announcement-preview--plain', css)
        self.assertIn('border:0!important', css)
        self.assertIn('max-width:1280px', css)
