"""Admin directory UI contract tests (no database fixtures required)."""
from django.core.paginator import Paginator
from django.template import Context, Template
from django.test import SimpleTestCase


class AdminJobBoardUiTests(SimpleTestCase):
    def test_pagination_preserves_filters_and_escapes_values(self):
        page = Paginator(list(range(65)), 20).page(2)
        template = Template(
            "{% load admin_directory_pagination %}"
            "{% admin_directory_pagination page filters 'jobs' %}"
        )
        html = template.render(Context({
            'page': page,
            'filters': 'q=network+agent&state=active&source_type=EXTERNAL',
        }))
        self.assertIn('q=network+agent&amp;state=active&amp;source_type=EXTERNAL&amp;page=1', html)
        self.assertIn('q=network+agent&amp;state=active&amp;source_type=EXTERNAL&amp;page=3', html)
        self.assertIn('aria-current="page"', html)
        self.assertIn('Showing', html)
        self.assertIn('65', html)

    def test_first_page_has_disabled_previous_and_a_working_next(self):
        page = Paginator(list(range(45)), 20).page(1)
        html = Template(
            "{% load admin_directory_pagination %}"
            "{% admin_directory_pagination page '' 'jobs' %}"
        ).render(Context({'page': page}))
        self.assertIn('aria-disabled="true"', html)
        self.assertIn('href="?page=2"', html)

    def test_last_page_has_disabled_next(self):
        page = Paginator(list(range(41)), 20).page(3)
        html = Template(
            "{% load admin_directory_pagination %}"
            "{% admin_directory_pagination page '' 'jobs' %}"
        ).render(Context({'page': page}))
        self.assertIn('aria-disabled="true"', html)
        self.assertIn('Page 3, current page', html)

    def test_one_page_omits_numbered_nav_but_shows_count(self):
        page = Paginator(list(range(3)), 20).page(1)
        html = Template(
            "{% load admin_directory_pagination %}"
            "{% admin_directory_pagination page '' 'jobs' %}"
        ).render(Context({'page': page}))
        self.assertIn('of', html)
        self.assertNotIn('staff-page-numbers', html)
