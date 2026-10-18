"""Full-name/wildcard directory matching and correctly filtered alumni totals.

Run with an isolated Django test database; never against the production database.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Alumni


@override_settings(
    SECURE_SSL_REDIRECT=False,
    MIDDLEWARE=[
        middleware for middleware in settings.MIDDLEWARE
        if middleware != 'setup.middleware.SetupRequiredMiddleware'
    ],
)
class AlumniDirectoryPriorityOneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_superuser('directory_admin', 'directory_admin@example.com', 'pass')
        cls.member = User.objects.create_user('directory_member', 'directory_member@example.com', 'pass')
        cls.first = cls.add_alumnus('Renalyn', 'Andam', 'CTE', 'BEED', 2025)
        cls.second = cls.add_alumnus('Renato', 'Santos', 'CTE', 'BEED', 2025)
        cls.third = cls.add_alumnus('Renalyn', 'Del Rosario', 'CIT', 'BSINT', 2025)
        cls.fourth = cls.add_alumnus('Maria', 'Andam', 'CTE', 'BEED', 2024)

    @classmethod
    def add_alumnus(cls, first, last, college, course, year):
        User = get_user_model()
        user = User.objects.create_user(
            username=f'user_{first.lower()}_{last.lower().replace(" ", "_")}',
            email=f'{first.lower()}.{last.lower().replace(" ", "_")}@example.com',
            password='pass', first_name=first, last_name=last,
        )
        return Alumni.objects.create(
            user=user, college=college, campus='MAIN',
            graduation_year=year, course=course, gender='F',
            city='Dumaguete', province='Negros Oriental',
            address='',
        )

    def request_directory(self, user, params):
        self.client.force_login(user)
        return self.client.get(reverse('alumni_directory:alumni_list'), params, secure=True)

    def test_plain_full_name_matches_across_user_fields(self):
        response = self.request_directory(self.member, {'search': 'Renalyn Andam'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_registered'], 1)
        self.assertEqual([a.pk for a in response.context['alumni_list']], [self.first.pk])

    def test_name_token_matches_with_middle_name(self):
        self.first.user.first_name = 'Renalyn Mae'
        self.first.user.save(update_fields=['first_name'])
        response = self.request_directory(self.member, {'search': 'Renalyn Andam'})
        self.assertEqual(response.context['total_registered'], 1)

    def test_partial_and_wildcard_name_search(self):
        for search, expected in (
            ('Ren*', 3), ('*Andam', 2), ('Ren*Andam', 1),
            ('Renalyn', 2), ('rEnAlYn aNdAm', 1),
        ):
            with self.subTest(search=search):
                response = self.request_directory(self.member, {'search': search})
                self.assertEqual(response.context['total_registered'], expected)

    def test_regex_punctuation_is_literal_not_executable(self):
        for query in ('R.*', '*****', ','):
            with self.subTest(query=query):
                response = self.request_directory(self.member, {'search': query})
                self.assertEqual(response.context['total_registered'], 0)

    def test_filters_are_combined_and_count_is_not_page_size(self):
        response = self.request_directory(self.staff, {
            'graduation_year': '2025', 'college': 'CTE', 'course': 'BEED',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_registered'], 2)
        self.assertEqual(response.context['total_alumni'], 4)
        self.assertContains(response, 'Matching Alumni')
        self.assertContains(response, 'Out of 4 total alumni')
        self.assertCountEqual([a.pk for a in response.context['alumni_list']], [self.first.pk, self.second.pk])

    def test_name_and_filters_intersect(self):
        response = self.request_directory(self.staff, {
            'search': 'Ren*', 'graduation_year': '2025',
            'college': 'CTE', 'course': 'BEED',
        })
        self.assertEqual(response.context['total_registered'], 2)
        response = self.request_directory(self.staff, {
            'search': 'Renalyn Andam', 'graduation_year': '2024',
            'college': 'CTE', 'course': 'BEED',
        })
        self.assertEqual(response.context['total_registered'], 0)

    def test_regular_member_still_cannot_apply_restricted_academic_filters(self):
        response = self.request_directory(self.member, {
            'search': 'Renalyn', 'college': 'CTE', 'graduation_year': '2024',
        })
        self.assertEqual(response.context['total_registered'], 2)
        self.assertNotContains(response, 'BSINT')

    def test_no_filter_keeps_existing_empty_directory_prompt(self):
        response = self.request_directory(self.staff, {})
        self.assertEqual(response.context['total_registered'], 0)
        self.assertFalse(response.context['show_alumni_results'])
        self.assertContains(response, 'Total Alumni')
        self.assertNotContains(response, 'Matching Alumni')
