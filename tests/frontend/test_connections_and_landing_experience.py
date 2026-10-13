"""Regressions for the connected-user deep link and public CMS landing experience.

Source-level checks work without a Django runtime; integration tests on a configured
Django database are still required before production deployment.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT / path).read_text(encoding='utf8')

class ConnectionsAndLandingExperienceTests(unittest.TestCase):
    def test_my_connections_messages_open_selected_user(self):
        template = source('templates/connections/my_connections.html')
        self.assertIn("{% url 'connections:conversations_list' %}?with={{ other_user.pk }}", template)
        self.assertNotIn('href="{% url \'connections:conversations_list\' %}"', template)

    def test_directory_shortcut_uses_the_same_backend_chat_flow(self):
        template = source('templates/alumni_directory/alumni_list.html')
        self.assertIn("{% url 'connections:conversations_list' %}?with={{ alumni.user_id }}", template)
        view = source('connections/views.py')
        self.assertIn("request.GET.get('with', '').strip()", view)
        self.assertIn('Connection.are_connected(request.user, recipient)', view)
        self.assertIn('DirectConversation.get_or_create_conversation(request.user, recipient)', view)
        self.assertIn("'selected_conversation_user_id': selected_conversation_user_id", view)
        self.assertIn('data-initial-chat-user-id=', source('templates/connections/conversations_list.html'))

    def test_new_public_styles_do_not_override_authenticated_layout(self):
        public_base = source('templates/base_landingpage.html')
        self.assertIn('block page_final_css', public_base)
        self.assertIn('css/home_experience.css', source('templates/home.html'))
        css = source('static/css/home_experience.css')
        self.assertIn('.home-experience .home-hero', css)
        self.assertNotIn('body.alumni-portal', css)

    def test_all_existing_home_modules_and_feedback_are_retained(self):
        home = source('templates/home.html')
        for value in ('features', 'announcements', 'upcoming_events',
                      'vmgo_section', 'alumni_statistics', 'testimonials',
                      'staff_members', 'faqs', 'feedback_form',
                      'name="office_website"', '{% csrf_token %}',
                      'site_config.hero_background_image',
                      '{{ hero_headline', '{{ hero_subheadline', 'cta_primary_text'):
            with self.subTest(value=value):
                self.assertIn(value, home)

    def test_campus_gallery_uses_actual_cms_data_and_no_mock_content(self):
        home = source('templates/home.html')
        view = source('core/views.py')
        self.assertIn('NORSUCampus.objects.filter(is_active=True)', view)
        self.assertIn('{% if norsu_campuses %}', home)
        self.assertIn('src="{{ campus.image.url }}"', home)
        self.assertIn('{{ campus.location }}', home)
        self.assertIn('data-home-gallery', home)
        self.assertNotIn('CMS campus title', home)
        self.assertNotIn('Example team member', home)

    def test_gallery_script_has_pause_controls_and_reduced_motion(self):
        js = source('static/js/home_gallery.js')
        for value in ('prefers-reduced-motion: reduce',
                      'data-gallery-toggle', 'aria-pressed',
                      'IntersectionObserver', 'visibilitychange',
                      'keydown', 'scrollToIndex', 'data-home-accordion'):
            self.assertIn(value, js)
        self.assertIn('home-gallery-progress', source('templates/home.html'))

if __name__ == '__main__':
    unittest.main()
