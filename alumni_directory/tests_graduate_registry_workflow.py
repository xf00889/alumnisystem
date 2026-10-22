"""Focused registry UX, compare/reconciliation, import confirmation and access checks."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse
from alumni_directory.models import GraduateRegistry
from alumni_directory.services.graduate_registry_import import compare_graduate_registry
from alumni_directory.tests_registrar_import_formats import fake_xlsx


def upload_roster():
    return SimpleUploadedFile('approved-roster.xlsx', fake_xlsx(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@override_settings(MIDDLEWARE=[mw for mw in settings.MIDDLEWARE if mw != 'setup.middleware.SetupRequiredMiddleware'])
class RegistryWorkflowTests(TestCase):
    def setUp(self):
        self.User=get_user_model()
        self.admin=self.User.objects.create_superuser('registry_administrator', 'regadmin@example.com', 'securepw')
        self.client.force_login(self.admin)
        self.list_url=reverse('alumni_directory:graduate_registry')
        self.compare_url=reverse('alumni_directory:registry_compare')
        self.import_url=reverse('alumni_directory:registry_import')

    def test_registry_separate_from_registered_alumni_and_displays_navigation(self):
        response=self.client.get(self.list_url)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Graduate Registry &amp; Verification')
        self.assertContains(response,'Compare with registry')
        registered=self.client.get(reverse('alumni_directory:alumni_management'))
        self.assertContains(registered,'Graduate Registry')
        self.assertNotContains(registered,'registryImportModal')

    def test_preview_does_not_modify_database_and_import_requires_confirmation(self):
        post={'registry_file':upload_roster(),'campus':'BSC'}
        response=self.client.post(self.compare_url, post)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['totals']['new'],3)
        self.assertEqual(GraduateRegistry.objects.count(),0)
        rejected=self.client.post(self.import_url,{'registry_file':upload_roster(),'campus':'BSC'})
        self.assertEqual(rejected.status_code,400)
        self.assertEqual(GraduateRegistry.objects.count(),0)
        applied=self.client.post(self.import_url, {'registry_file':upload_roster(),'campus':'BSC','confirmed':'yes'})
        self.assertEqual(applied.status_code,200)
        self.assertEqual(applied.json()['created'],3)
        self.assertEqual(GraduateRegistry.objects.count(),3)
        rechecked=self.client.post(self.compare_url,{'registry_file':upload_roster(),'campus':'BSC'})
        self.assertEqual(rechecked.json()['totals']['unchanged'],3)
        self.assertEqual(rechecked.json()['totals']['new'],0)

    def test_registry_list_filters_by_year_campus_claim_and_search(self):
        GraduateRegistry.objects.create(first_name='Mila',last_name='Sunrise',campus='BSC',graduation_year=2025,course='BEED',college='CTE')
        GraduateRegistry.objects.create(first_name='Paolo',last_name='Sunrise',campus='MAIN',graduation_year=2023,course='BSIT',college='CAS',claimed_by=self.admin)
        response=self.client.get(self.list_url, {'year':'2025','campus':'BSC','college':'CTE','status':'available','q':'Mila'})
        self.assertContains(response,'Mila')
        self.assertNotContains(response,'Paolo')
        self.assertEqual(response.context['registry_filtered'],1)
        self.assertEqual(response.context['registry_available'],1)
        self.assertEqual(response.context['registry_claimed'],1)

    def test_claimed_conflicts_are_review_only_and_never_overwritten(self):
        owner=self.User.objects.create_user('claim_owner','owner@example.com','pw')
        entry=GraduateRegistry.objects.create(first_name='Jo',last_name='Registrar',campus='BSC',graduation_year=2025,course='BACHELOR OF ELEMENTARY EDUCATION',claimed_by=owner)
        preview=self.client.post(self.compare_url,{'registry_file':upload_roster(),'campus':'BSC'}).json()
        self.assertEqual(preview['totals']['review'],1)
        saved=self.client.post(self.import_url,{'registry_file':upload_roster(),'campus':'BSC','confirmed':'yes'}).json()
        self.assertEqual(saved['created'],2)
        self.assertEqual(saved['skipped'],1)
        entry.refresh_from_db()
        self.assertEqual(entry.claimed_by,owner)
        self.assertEqual(entry.suffix,'')

    def test_duplicate_uploaded_records_are_flagged(self):
        body=(b'First Name,Last Name,Graduation Year,Campus,Program\n'
              b'Sara,Learner,2025,BSC,BSIT\n'
              b'Sara,Learner,2025,BSC,BSIT\n')
        preview=self.client.post(self.compare_url,{'registry_file':SimpleUploadedFile('duplicates.csv',body),'campus':'BSC'}).json()
        self.assertEqual(preview['totals']['new'],1)
        self.assertEqual(preview['totals']['review'],1)
        self.assertEqual(GraduateRegistry.objects.count(),0)

    def test_comparison_csv_export_is_read_only(self):
        response=self.client.post(self.compare_url,{'registry_file':upload_roster(),'campus':'BSC','download':'csv'})
        self.assertEqual(response.status_code,200)
        self.assertIn('text/csv',response['Content-Type'])
        self.assertIn('Source row',response.content.decode())
        self.assertEqual(GraduateRegistry.objects.count(),0)

    def test_missing_campus_rejected_without_changes(self):
        response=self.client.post(self.compare_url,{'registry_file':upload_roster(),'campus':''})
        self.assertEqual(response.status_code,400)
        self.assertEqual(GraduateRegistry.objects.count(),0)

    def test_regular_user_cannot_view_or_upload(self):
        regular=self.User.objects.create_user('unprivileged','ordinary@example.com','pw')
        self.client.force_login(regular)
        self.assertNotEqual(self.client.get(self.list_url).status_code,200)
        before=GraduateRegistry.objects.count()
        response=self.client.post(self.import_url,{'registry_file':upload_roster(),'campus':'BSC','confirmed':'yes'})
        self.assertNotEqual(response.status_code,200)
        self.assertEqual(GraduateRegistry.objects.count(),before)

    def test_hr_staff_cannot_manage_university_registry(self):
        hr=self.User.objects.create_user('hr_only_user','hr_registry@example.com','pw',is_staff=True)
        hr.profile.is_hr=True
        hr.profile.save(update_fields=['is_hr'])
        self.client.force_login(hr)
        self.assertNotEqual(self.client.get(self.list_url).status_code,200)
        self.assertNotEqual(self.client.post(self.compare_url,{'registry_file':upload_roster(),'campus':'BSC'}).status_code,200)
