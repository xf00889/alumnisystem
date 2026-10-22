"""Graduate Registry reconciliation UX: differences only, safe comparisons, no writes."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from alumni_directory.models import GraduateRegistry


def csv_roster(text):
    return SimpleUploadedFile('registrar_review.csv', text.encode('utf-8'), content_type='text/csv')


HEAD = 'First Name,Last Name,Graduation Year,Campus,Program,Middle Name\n'


@override_settings(MIDDLEWARE=[mw for mw in settings.MIDDLEWARE if mw != 'setup.middleware.SetupRequiredMiddleware'])
class GraduateRegistryReviewUxTests(TestCase):
    def setUp(self):
        User = get_user_model()
        admin = User.objects.create_superuser('registry_review_admin', 'review_admin@example.com', 'safePW')
        self.client.force_login(admin)
        self.compare_url = reverse('alumni_directory:registry_compare')
        self.registry_url = reverse('alumni_directory:graduate_registry')

    def test_exact_matches_return_no_rows_in_comparison_preview(self):
        GraduateRegistry.objects.create(first_name='Ana', last_name='Reyes', campus='BSC', graduation_year=2025, course='BSIT')
        roster = HEAD + 'Ana,Reyes,2025,BSC,BSIT,\n'
        response = self.client.post(self.compare_url, {'registry_file': csv_roster(roster), 'campus': 'BSC'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals']['unchanged'], 1)
        self.assertEqual(data['total_rows'], 0)
        self.assertEqual(data['rows'], [])
        self.assertEqual(GraduateRegistry.objects.count(), 1)

    def test_new_and_changed_separately_without_existing_matches(self):
        GraduateRegistry.objects.create(first_name='Ana', last_name='Reyes', campus='BSC', graduation_year=2025, course='BSIT')
        GraduateRegistry.objects.create(first_name='Ben', last_name='Cruz', campus='BSC', graduation_year=2025, course='BSIT')
        roster = HEAD + ('Ana,Reyes,2025,BSC,BSIT,\n'
                         'Ben,Cruz,2025,BSC,BSIT,Q\n'
                         'Cara,Santos,2025,BSC,BSIT,\n')
        response = self.client.post(self.compare_url, {'registry_file': csv_roster(roster), 'campus': 'BSC'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals']['unchanged'], 1)
        self.assertEqual(data['totals']['update'], 1)
        self.assertEqual(data['totals']['new'], 1)
        self.assertEqual(data['total_rows'], 2)
        self.assertEqual({r['status'] for r in data['rows']}, {'new', 'update'})
        updated = next(r for r in data['rows'] if r['status'] == 'update')
        self.assertIn('Middle Name:', updated['changes'])
        self.assertIn('(blank) → Q', updated['changes'])
        self.assertEqual(GraduateRegistry.objects.count(), 2)

    def test_difference_csv_excludes_exact_matches_and_is_read_only(self):
        GraduateRegistry.objects.create(first_name='Ana', last_name='Reyes', campus='BSC', graduation_year=2025, course='BSIT')
        roster = HEAD + 'Ana,Reyes,2025,BSC,BSIT,\nCara,Santos,2025,BSC,BSIT,\n'
        response = self.client.post(self.compare_url, {
            'registry_file': csv_roster(roster), 'campus': 'BSC', 'download': 'csv',
        })
        self.assertEqual(response.status_code, 200)
        csv_text = response.content.decode()
        self.assertIn('Santos, Cara', csv_text)
        self.assertNotIn('Reyes,', csv_text)
        self.assertEqual(GraduateRegistry.objects.count(), 1)

    def test_native_dialog_and_compact_comparison_controls_exist(self):
        response = self.client.get(self.registry_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="grBusyDialog"')
        self.assertContains(response, 'id="grFeedbackDialog"')
        self.assertContains(response, 'id="grTabDifferences"')
        self.assertContains(response, 'id="grTabNew"')
        self.assertContains(response, 'id="registry-compare"')
