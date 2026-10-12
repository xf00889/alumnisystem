"""Regression tests for mentor-directory grouping and review decisions."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Education, Mentor, MentorApplication, Profile
from accounts.templatetags.string_filters import split
from setup.models import SetupState


class MentorManagementUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()
        User = get_user_model()
        cls.admin = User.objects.create_superuser(
            username='mentor-admin', email='mentor-admin@example.com', password='TestOnly123!'
        )
        cls.mentor_user = User.objects.create_user(
            username='mentor-ux', email='mentor-ux@example.com',
            first_name='Mentor', last_name='Example', password='TestOnly123!'
        )
        mentor_profile, _ = Profile.objects.get_or_create(user=cls.mentor_user)
        Education.objects.create(profile=mentor_profile, graduation_year=2022, is_primary=True)
        Mentor.objects.create(
            user=cls.mentor_user, expertise_areas='Web Developer, Data Science',
            accepting_mentees=True, is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_multiword_expertise_is_single_label(self):
        self.assertEqual(split('Web Developer, Data Science'), ['Web Developer', 'Data Science'])
        self.assertEqual(split(' Web Developer , , Data Science '), ['Web Developer', 'Data Science'])

    def test_expertise_and_batch_can_be_combined(self):
        response = self.client.get(reverse('accounts:admin_mentor_list'), {
            'expertise': 'web developer', 'batch': '2022',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filtered_count'], 1)
        self.assertEqual(response.context['mentors'][0].expertise_labels,
                         ['Web Developer', 'Data Science'])
        self.assertEqual(response.context['mentors'][0].graduation_batch, 2022)

    def test_invalid_review_does_not_change_application_status(self):
        application = MentorApplication.objects.create(
            user=self.mentor_user, expertise_areas='Web Developer',
            years_of_experience=2, competency_summary='Software development',
        )
        response = self.client.post(
            reverse('accounts:review_mentor_application', args=[application.pk]),
            {'review_notes': 'A note without a decision'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        application.refresh_from_db()
        self.assertEqual(application.status, 'PENDING')
