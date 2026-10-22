"""Focused tests for CSV/XLSX registrar lists and the importing UI.

Run: python manage.py test alumni_directory.tests_registrar_import_formats
"""
import io
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from alumni_directory.models import GraduateRegistry
from alumni_directory.services.graduate_registry_import import import_graduate_registry


def fake_xlsx():
    """Tiny standards-compliant workbook shaped like the research roster."""
    main = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rows = [
        ('A8', 'LISTS OF CANDIDATES FOR GRADUATION, SY 2024-2025'),
        ('A16', 'COLLEGE OF TEACHER EDUCATION'),
        ('A17', 'BACHELOR OF ELEMENTARY EDUCATION'),
        ('A18', 'Area of Concentration: General Curriculum'),
        ('A20', '*1'), ('B20', 'Mary Ann'), ('C20', 'L.'), ('D20', 'Example'),
        ('A21', '2'), ('B21', 'Jo'), ('D21', 'Registrar'), ('E21', 'Jr.'),
        ('A22', 'COLLEGE OF ARTS AND SCIENCES'),
        ('A23', 'BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY'),
        ('A24', '1'), ('B24', 'Rhea'), ('C24', 'Q.'), ('D24', 'Learner'),
    ]
    buckets = {}
    for ref, value in rows:
        rowid = ''.join(char for char in ref if char.isdigit())
        buckets.setdefault(rowid, []).append((ref, value))
    sheetdata = ''.join('<row r="{r}">{cells}</row>'.format(
        r=r, cells=''.join(f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>' for ref, value in cells)
    ) for r,cells in sorted(buckets.items(),key=lambda x:int(x[0])))
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml',
            f'<workbook xmlns="{main}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="GRAD 2026" sheetId="1" r:id="rId1" /></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml" />'
            '</Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{main}"><sheetData>{sheetdata}</sheetData></worksheet>')
    return output.getvalue()


@override_settings(MIDDLEWARE=[
    middleware for middleware in settings.MIDDLEWARE
    if middleware != "setup.middleware.SetupRequiredMiddleware"
])
class RegistrarImportFormatTests(TestCase):
    def test_xlsx_section_headings_middle_suffix_and_year_marker(self):
        upload = SimpleUploadedFile('research.xlsx', fake_xlsx())
        result = import_graduate_registry(upload, default_campus='BSC')
        self.assertEqual((result.created, result.skipped), (3, 0))
        student = GraduateRegistry.objects.get(last_name='Example')
        self.assertEqual(student.first_name, 'Mary Ann')
        self.assertEqual(student.middle_name, 'L.')
        self.assertEqual(student.graduation_year, 2024)
        self.assertEqual(student.college, 'CTE')
        self.assertEqual(student.major, 'General Curriculum')
        self.assertEqual(GraduateRegistry.objects.get(last_name='Registrar').suffix, 'Jr.')
        self.assertEqual(GraduateRegistry.objects.get(last_name='Learner').graduation_year, 2025)
        self.assertEqual(GraduateRegistry.objects.get(last_name='Learner').college, 'CAS')

    def test_tab_name_2026_does_not_override_school_year_2025(self):
        upload = SimpleUploadedFile('grad.xlsx', fake_xlsx())
        import_graduate_registry(upload)
        self.assertFalse(GraduateRegistry.objects.filter(graduation_year=2026).exists())

    def test_headerless_2020_2021_csv_uses_filename_year(self):
        source = (
            'COLLEGE OF ARTS AND SCIENCES,,,,\r\n'
            'BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY,,,,\r\n'
            '1,Anna Marie,B.,Tester,\r\n'
        ).encode('utf-8')
        upload = SimpleUploadedFile('LIST OF GRADUATES 2020-2021.csv', source)
        result = import_graduate_registry(upload)
        self.assertEqual(result.created, 1)
        record = GraduateRegistry.objects.get()
        self.assertEqual(record.graduation_year, 2021)
        self.assertEqual(record.college, 'CAS')
        self.assertEqual(record.middle_name, 'B.')

    def test_standard_csv_remains_supported_and_preserves_existing_email(self):
        payload = (b'FullName,Year-1,Course Grad,Campus,Email Address\n'
                   b'"Graduate, Test",2024,BSINT,NORSU-BSC,test@example.com\n')
        first = import_graduate_registry(SimpleUploadedFile('list.csv',payload))
        second = import_graduate_registry(SimpleUploadedFile('list.csv',payload))
        self.assertEqual((first.created, second.created, second.updated), (1,0,1))
        self.assertEqual(GraduateRegistry.objects.count(), 1)
        self.assertEqual(GraduateRegistry.objects.get().email, 'test@example.com')

    def test_claimed_record_stays_linked_on_reimport(self):
        User = get_user_model()
        owner = User.objects.create_user(username='claimedowner', password='testpw')
        entry = GraduateRegistry.objects.create(
            first_name='Jo', last_name='Registrar', campus='BSC',
            graduation_year=2025, course='BEED', claimed_by=owner,
        )
        import_graduate_registry(SimpleUploadedFile('research.xlsx',fake_xlsx()))
        entry.refresh_from_db()
        self.assertEqual(entry.claimed_by,owner)
        self.assertEqual(entry.course, 'BEED')

    def test_does_not_create_accounts_and_returns_json_to_admin(self):
        User = get_user_model()
        staff = User.objects.create_superuser('gradadmin', 'gradadmin@example.com', 'testpw')
        self.client.force_login(staff)
        before = User.objects.count()
        response = self.client.post(
            reverse('alumni_directory:alumni_management'),
            {'import_registry_csv':'1','registry_campus':'BSC',
             'registry_csv_file': SimpleUploadedFile('research.xlsx',fake_xlsx())},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['created'],3)
        self.assertEqual(response.json()['skipped'],0)
        self.assertEqual(User.objects.count(),before)

    def test_invalid_extension_rejected_without_database_changes(self):
        with self.assertRaisesMessage(ValueError,'Only .csv and .xlsx'):
            import_graduate_registry(SimpleUploadedFile('list.pdf',b'not a spreadsheet'))
        self.assertEqual(GraduateRegistry.objects.count(),0)

    def test_yearless_unstructured_document_not_imported(self):
        upload=SimpleUploadedFile('registrar.csv',b'COLLEGE OF ARTS AND SCIENCES\nBACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY\n1,Student,,Tester\n')
        with self.assertRaisesMessage(ValueError,'No valid graduate rows'):
            import_graduate_registry(upload)
        self.assertEqual(GraduateRegistry.objects.count(),0)

    def test_import_modal_shows_progress_area_and_accepts_xlsx(self):
        User=get_user_model()
        admin=User.objects.create_superuser('test_import_ui','ui@example.com','pw')
        self.client.force_login(admin)
        response=self.client.get(reverse('alumni_directory:alumni_management'))
        self.assertContains(response,'registryImportProgress')
        self.assertContains(response,'graduate-registry-import.js')
        self.assertContains(response,'.csv,.xlsx')
