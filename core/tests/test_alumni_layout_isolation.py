"""Regression checks for alumni-only presentation selection.

No database is required. Run with:
    python -m unittest core.tests.test_alumni_layout_isolation
"""
import unittest
from types import SimpleNamespace

from core.context_processors import user_role_context


class AlumniLayoutIsolationTests(unittest.TestCase):
    APPS = ('core', 'accounts', 'alumni_directory', 'jobs', 'mentorship',
            'alumni_groups', 'connections', 'events', 'announcements',
            'donations', 'surveys', 'feedback')
    INTERACTIVE = {'accounts', 'alumni_directory', 'jobs', 'mentorship',
                   'alumni_groups', 'connections', 'events', 'announcements',
                   'donations', 'surveys', 'feedback'}

    def make_request(self, app_name, *, authenticated=True, staff=False,
                     superuser=False, coordinator=False, hr=False):
        profile = SimpleNamespace(is_alumni_coordinator=coordinator, is_hr=hr)
        user = SimpleNamespace(is_authenticated=authenticated, is_staff=staff,
                               is_superuser=superuser, profile=profile)
        return SimpleNamespace(user=user,
                               resolver_match=SimpleNamespace(app_name=app_name))

    def test_regular_alumni_only_uses_alumni_layout(self):
        roles = (
            ('alumni', {}, True),
            ('staff', {'staff': True}, False),
            ('superuser', {'superuser': True}, False),
            ('coordinator', {'coordinator': True}, False),
            ('hr', {'hr': True}, False),
            ('anonymous', {'authenticated': False}, False),
        )
        for role_name, flags, alumni_expected in roles:
            for app_name in self.APPS:
                with self.subTest(role=role_name, app=app_name):
                    result = user_role_context(self.make_request(app_name, **flags))
                    self.assertEqual(result['use_alumni_layout'], alumni_expected)
                    self.assertEqual(result['alumni_page_base'],
                                     'base_alumni.html' if alumni_expected else 'base.html')
                    self.assertEqual(result['load_alumni_feature_scripts'],
                                     alumni_expected and app_name in self.INTERACTIVE)
                    self.assertEqual(result['tracer_study_page_base'],
                                     'base_landingpage.html' if role_name == 'anonymous'
                                     else ('base_alumni.html' if alumni_expected else 'base.html'))


if __name__ == '__main__':
    unittest.main()
