"""Enforce the registrar workflow on the server, not only with disabled buttons."""
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import GraduateRegistry


HEAD = 'First Name,Last Name,Graduation Year,Campus,Program,Middle Name\n'
ROSTER = HEAD + 'Ana,Reyes,2025,BSC,BSIT,\nBen,Cruz,2025,BSC,BSIT,\n'


def file_upload(text=ROSTER):
    return SimpleUploadedFile('approved.csv', text.encode('utf-8'), content_type='text/csv')


@override_settings(MIDDLEWARE=[mw for mw in settings.MIDDLEWARE if mw != 'setup.middleware.SetupRequiredMiddleware'])
class RegistryReviewReceiptTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser('graduate_receipt_admin', 'receipt@example.com', 'pw')
        self.client.force_login(self.admin)
        self.compare = reverse('alumni_directory:registry_compare')
        self.apply = reverse('alumni_directory:registry_import')

    def preview(self, text=ROSTER):
        r = self.client.post(self.compare, {'registry_file': file_upload(text), 'campus': 'BSC'})
        self.assertEqual(r.status_code, 200)
        return r.json()['review_receipt']

    def submit(self, *, receipt='', text=ROSTER, campus='BSC', year=''):
        return self.client.post(self.apply, {
            'registry_file': file_upload(text), 'campus': campus,
            'year_fallback': year, 'confirmed': 'yes', 'review_receipt': receipt,
        })

    def test_confirm_without_comparison_receipt_is_rejected_without_writes(self):
        response = self.submit()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 0)

    def test_valid_comparison_receipt_imports_and_prevents_duplicate_reimport(self):
        receipt = self.preview()
        self.assertEqual(GraduateRegistry.objects.count(), 0)
        result = self.submit(receipt=receipt)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['created'], 2)
        self.assertEqual(GraduateRegistry.objects.count(), 2)
        stale = self.submit(receipt=receipt)
        self.assertEqual(stale.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 2)

    def test_changed_file_is_rejected(self):
        receipt = self.preview()
        tampered = HEAD + 'Ana,Reyes,2025,BSC,BSIT,\nCara,Santos,2025,BSC,BSIT,\n'
        response = self.submit(receipt=receipt, text=tampered)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 0)

    def test_changed_campus_and_fallback_year_are_rejected(self):
        receipt = self.preview()
        r = self.submit(receipt=receipt, campus='MAIN')
        self.assertEqual(r.status_code, 400)
        r = self.submit(receipt=receipt, year='2025')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 0)

    def test_receipt_cannot_be_used_by_another_administrator(self):
        receipt = self.preview()
        other = get_user_model().objects.create_superuser('second_admin', 'admin2@example.com', 'pw')
        self.client.force_login(other)
        response = self.submit(receipt=receipt)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 0)

    def test_registry_change_after_preview_requires_new_review(self):
        receipt = self.preview()
        GraduateRegistry.objects.create(first_name='Ana', last_name='Reyes', campus='BSC', graduation_year=2025, course='BSIT')
        response = self.submit(receipt=receipt)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 1)

    def test_expired_receipt_requires_new_review(self):
        receipt = self.preview()
        with patch('alumni_directory.registry_views.COMPARISON_RECEIPT_MAX_AGE', -1):
            response = self.submit(receipt=receipt)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 0)

    def test_all_matched_receipt_cannot_write(self):
        GraduateRegistry.objects.create(first_name='Ana', last_name='Reyes', campus='BSC', graduation_year=2025, course='BSIT')
        GraduateRegistry.objects.create(first_name='Ben', last_name='Cruz', campus='BSC', graduation_year=2025, course='BSIT')
        receipt = self.preview()
        response = self.submit(receipt=receipt)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GraduateRegistry.objects.count(), 2)
