"""Focused source-level guards for shared alumni navigation and mobile chat.

These checks do not require Django or a database. Run with:
python -m unittest discover -s tests/frontend -p 'test_mobile_chat_connections_navigation.py' -v
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MobileChatAndConnectionsNavigationTests(unittest.TestCase):
    def source(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_shared_desktop_mobile_tab_points_to_connections(self):
        source = self.source('templates/alumni/components/primary_navigation_links.html')
        self.assertIn("{% url 'connections:my_connections' %}", source)
        self.assertIn('<span>Connections</span>', source)
        self.assertNotIn('<span>Requests</span>', source)
        self.assertEqual(source.count('alumni-primary-link alumni-primary-link--{{ navigation_variant }}'), 5)

    def test_requests_and_profile_remain_in_more(self):
        more = self.source('templates/alumni/components/secondary_navigation_links.html')
        navigation = self.source('templates/alumni/components/navigation.html')
        self.assertIn("{% url 'connections:connection_requests' %}", more)
        self.assertIn('data-connection-request-count', more)
        self.assertIn("{% url 'accounts:profile_detail' %}", navigation)
        self.assertIn('My profile', navigation)
        self.assertIn("request.resolver_match.url_name == 'connection_requests'", navigation)

    def test_mobile_messages_keep_history_scrolling_inside_chat_panel(self):
        css = self.source('static/css/alumni/messaging-workspace.css')
        self.assertIn('grid-template-rows: auto minmax(0, 1fr) auto !important;', css)
        self.assertIn('grid-row: 2;', css)
        self.assertIn('grid-row: 3;', css)
        self.assertIn('overflow-y: auto !important;', css)
        self.assertIn('--norsu-chat-visual-height', css)
        self.assertIn('fe-page--connections-conversations-list-html', css)
        self.assertIn('.alumni-bottom-nav', css)

    def test_mobile_scroll_handles_reverse_and_normal_threads(self):
        js = self.source('static/js/alumni/messaging-workspace.js')
        self.assertIn("getComputedStyle(scroller).flexDirection === 'column-reverse'", js)
        self.assertIn('window.visualViewport?.addEventListener', js)
        self.assertIn('scrollChatToLatest', js)


if __name__ == '__main__':
    unittest.main()
