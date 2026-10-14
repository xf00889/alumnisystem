"""Regression coverage for extended alumni fields in Django admin and exports.

Run on the project's configured Django test database:
    python manage.py test accounts.tests_profile_admin_coverage -v 2
"""
from django.contrib import admin
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.admin import ProfileAdmin
from accounts.models import Profile
from core.export_utils import ModelExporter


class ProfileAdminCoverageTests(SimpleTestCase):
    def test_every_extended_field_is_editable_in_django_admin(self):
        extended_fields = {
            'birth_place', 'civil_status', 'middle_name', 'maiden_name',
            'landline_number', 'education_level', 'employer_sector',
            'employment_address', 'workplace_reference_name',
            'workplace_reference_position', 'workplace_reference_contact',
            'emergency_contact_name', 'emergency_contact_relationship',
            'emergency_contact_number',
        }
        model_admin = ProfileAdmin(Profile, admin.site)
        included_fields = {
            field
            for _title, options in model_admin.fieldsets
            for field in options.get('fields', ())
            if isinstance(field, str)
        }
        self.assertTrue(extended_fields.issubset(included_fields))
        self.assertIn('is_alumni_coordinator', included_fields)
        self.assertIn('is_hr', included_fields)

    def test_regular_alumni_export_omits_private_contact_fields(self):
        config = ModelExporter.get_alumni_export_config()
        columns = config['field_names']
        self.assertIn('user__profile__education_level', columns)
        self.assertIn('user__profile__employer_sector', columns)
        self.assertNotIn('user__profile__emergency_contact_number', columns)
        self.assertNotIn('user__profile__workplace_reference_contact', columns)
        self.assertEqual(len(config['field_names']), len(config['field_labels']))


class DirectoryBulkExportPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.member = User.objects.create_user(
            username='directory_member', email='directory_member@example.com',
            password='difficult-test-password'
        )

    def test_member_cannot_download_directory_csv(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('alumni_directory:tabular_alumni_list'), {'format': 'csv'})
        self.assertEqual(response.status_code, 403)

    def test_member_directory_page_does_not_show_export_control(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('alumni_directory:tabular_alumni_list'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['can_export_alumni'])
