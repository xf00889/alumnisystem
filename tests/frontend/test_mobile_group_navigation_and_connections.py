"""Source-level regressions for compact mobile alumni community presentation."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

class MobileCommunityRefinementTests(unittest.TestCase):
    def test_last_stylesheet_wins_over_module_css(self):
        html = read('templates/base_alumni.html')
        self.assertIn('mobile-community-refinement.css', html)
        self.assertGreater(html.index('mobile-community-refinement.css'), html.index('{% block extra_css %}'))

    def test_mobile_brand_uses_existing_logo_asset(self):
        html = read('templates/alumni/components/navigation.html')
        self.assertIn("{% static 'images/alumni_logo.webp' %}", html)
        self.assertTrue((ROOT / 'static/images/alumni_logo.webp').exists())
        self.assertIn('alumni-brand-text', html)

    def test_message_badge_anchors_to_icon_and_reuses_unread_binding(self):
        html = read('templates/alumni/components/primary_navigation_links.html')
        self.assertIn('class="alumni-nav-icon-wrap"', html)
        self.assertIn('data-message-unread-count hidden', html)
        self.assertIn('Messages</span>', html)

    def test_connections_icons_include_every_action_and_labels(self):
        html = read('templates/connections/my_connections.html')
        self.assertIn('connection-actions--icons', html)
        self.assertIn('aria-label="Message ', html)
        self.assertIn('aria-label="View profile for ', html)
        self.assertIn('aria-label="Remove connection with ', html)
        self.assertNotIn('data-bs-toggle="dropdown"', html)

    def test_connections_still_routes_to_selected_user_conversation(self):
        html = read('templates/connections/my_connections.html')
        self.assertIn("{% url 'connections:conversations_list' %}?with={{ other_user.pk }}", html)
        self.assertIn("{% url 'connections:remove_connection' 0 %}", html)
        self.assertIn("{% url 'alumni_directory:alumni_detail' other_user.alumni.id %}", html)

    def test_connection_removal_uses_data_attributes_not_inline_js(self):
        html = read('templates/connections/my_connections.html')
        self.assertIn('class="btn btn-outline-danger connection-icon-action remove-connection-trigger"', html)
        self.assertNotIn('onclick="removeConnection(', html)
        self.assertIn('button.dataset.userName', html)
        self.assertIn('connectionsGrid.style.display = \'\'', html)

    def test_connections_profile_uses_real_avatar_field(self):
        html = read('templates/connections/my_connections.html')
        self.assertIn('other_user.profile.avatar.url', html)
        self.assertNotIn('other_user.profile.profile_picture', html)

    def test_group_list_and_moderation_selectors_exist(self):
        css = read('static/css/alumni/mobile-community-refinement.css')
        for name in ('group-list','group-detail','group-map','manage-members','group-feed-posts','group-composer','groupTabs'):
            self.assertIn(name,css)

    def test_mobile_timeline_has_no_nested_scroll(self):
        css = read('static/css/alumni/mobile-community-refinement.css')
        self.assertIn('max-height: none !important', css)
        self.assertIn('overflow: visible !important', css)
        js = read('static/js/alumni/group-feed.js')
        self.assertIn('holder.getBoundingClientRect().top', js)
        self.assertIn("holder.addEventListener('scroll'",js)
        self.assertIn("window.addEventListener('scroll'",js)

    def test_quiet_font_and_flat_card_rules_are_scoped_to_alumni(self):
        css = read('static/css/alumni/mobile-community-refinement.css')
        self.assertIn('body.alumni-portal .alumni-main[data-feature="alumni_groups"]', css)
        self.assertIn('font-size: .82rem', css)
        self.assertIn('box-shadow: none !important', css)

    def test_waiting_and_leaving_pages_are_included(self):
        for file in ['waiting_approval.html','leave_group_form.html']:
            html = read('templates/alumni_groups/'+file)
            self.assertIn('fe-page--alumni-groups-',html)
            self.assertIn('{% block content %}',html)

    def test_existing_group_list_switcher_is_restored_on_mobile(self):
        html = read('templates/alumni_groups/group_list.html')
        css = read('static/css/alumni/mobile-community-refinement.css')
        self.assertIn('document.documentElement.dataset.groupView = view', html)
        self.assertIn('[data-group-view="table"] .groups-grid', css)
        self.assertIn('[data-group-view="table"] .groups-table', css)
        self.assertIn('view-toggle-btn', css)

    def test_mobile_uses_regular_weight_inter(self):
        html = read('templates/base_alumni.html')
        css = read('static/css/alumni/mobile-community-refinement.css')
        self.assertIn('Inter:wght@400;500;600', html)
        self.assertIn("font-family: 'Inter', system-ui, sans-serif", css)

    def test_url_and_csrf_hooks_unchanged(self):
        for file in ['group_detail.html','manage_members.html','join_group_form.html']:
            content = read('templates/alumni_groups/'+file)
            self.assertIn('{% csrf_token %}',content)

if __name__ == '__main__':
    unittest.main()
