from django.contrib.auth import get_user_model
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings
from alumni_directory.models import Alumni

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class StaffProfileSeparationTests(TestCase):
    def setUp(self):
        setup_guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        self.addCleanup(setup_guard.stop)

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(username='staffonly', password='testpassword!',
                                             email='staff@example.com', is_staff=True)
        cls.dual = User.objects.create_user(username='alumniadmin', password='testpassword!',
                                            email='dual@example.com', is_staff=True)
        cls.alumnus = User.objects.create_user(username='graduate', password='testpassword!',
                                               email='graduate@example.com')
        for user in (cls.dual, cls.alumnus):
            Alumni.objects.create(user=user, college='CAS', campus='MAIN',
                                  graduation_year=2025, course='BSIT', gender='M',
                                  province='', city='', address='', is_verified=True)

    def test_staff_only_sees_admin_identity_not_alumni_profile(self):
        self.client.force_login(self.staff)
        resp=self.client.get(reverse('accounts:profile_detail'))
        self.assertRedirects(resp, reverse('accounts:staff_profile'))
        page=self.client.get(reverse('accounts:staff_profile'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Account Profile')
        self.assertNotContains(page, 'Apply as Mentor')
        self.assertNotContains(page, 'View my alumni profile')

    def test_staff_only_cannot_view_alumni_identity_or_apply_as_mentor(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('accounts:my_alumni_profile')).status_code,404)
        self.assertEqual(self.client.get(reverse('accounts:apply_mentor')).status_code,403)
        self.assertRedirects(self.client.get(reverse('accounts:edit_profile')),
                             reverse('accounts:edit_staff_profile'))

    def test_other_users_cannot_open_staff_only_profile_as_alumni(self):
        self.client.force_login(self.alumnus)
        self.assertEqual(self.client.get(reverse('accounts:profile_detail',args=[self.staff.username])).status_code,404)
        self.assertEqual(self.client.get(reverse('accounts:staff_profile')).status_code,403)

    def test_dual_role_has_two_separate_views(self):
        self.client.force_login(self.dual)
        self.assertRedirects(self.client.get(reverse('accounts:profile_detail')),
                             reverse('accounts:staff_profile'))
        self.assertContains(self.client.get(reverse('accounts:staff_profile')),
                            'View my alumni profile')
        self.assertEqual(self.client.get(reverse('accounts:my_alumni_profile')).status_code,200)

    def test_normal_alumnus_keeps_existing_profile(self):
        self.client.force_login(self.alumnus)
        self.assertEqual(self.client.get(reverse('accounts:profile_detail')).status_code,200)

    def test_staff_edit_only_changes_name_not_email_or_permissions(self):
        self.client.force_login(self.staff)
        response=self.client.post(reverse('accounts:edit_staff_profile'),
                                  {'first_name':'NORSU','last_name':'Staff',
                                   'email':'attacker@example.com', 'is_staff':'False'})
        self.assertRedirects(response, reverse('accounts:staff_profile'))
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.get_full_name(), 'NORSU Staff')
        self.assertEqual(self.staff.email, 'staff@example.com')
        self.assertTrue(self.staff.is_staff)

    def test_staff_only_alumni_section_post_blocked(self):
        self.client.force_login(self.staff)
        response=self.client.post(reverse('accounts:save_profile_section'), {'section':'skills'})
        self.assertEqual(response.status_code, 403)
