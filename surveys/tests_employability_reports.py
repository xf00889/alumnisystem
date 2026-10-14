"""Acceptance tests for the new staff employability report and public recovery route.
Run with: python manage.py test surveys.tests_employability_reports -v 2
"""
from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from alumni_directory.models import Alumni
from surveys.employability_reports import _aggregate
from surveys.models import EmploymentRecord


TEST_MIDDLEWARE = [m for m in settings.MIDDLEWARE if m != 'setup.middleware.SetupRequiredMiddleware']


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class EmployabilityReportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user('report-staff', 'staff@example.com', 'StrongPass123!', is_staff=True)
        self.visitor = User.objects.create_user('report-user', 'user@example.com', 'StrongPass123!')
        for user, name in ((self.admin,'Staff'), (self.visitor,'User')):
            user.profile.has_completed_registration = True
            user.profile.save(update_fields=['has_completed_registration'])
        self.a1 = self.create_alumni('first', 'MAIN', 'CAS')
        self.a2 = self.create_alumni('second', 'MAIN', 'CIT')
        self.a3 = self.create_alumni('third', 'BSC', 'CAS')
        EmploymentRecord.objects.create(alumni=self.a1, company_name='Acme',job_title='Analyst',industry='IT',start_date=date(2026,2,2))
        EmploymentRecord.objects.create(alumni=self.a1, company_name='Beta',job_title='Developer',industry='IT',start_date=date(2026,4,5))
        EmploymentRecord.objects.create(alumni=self.a3, company_name='Acme',job_title='Designer',industry='IT',start_date=date(2026,9,12))

    def create_alumni(self, username, campus, college):
        user = get_user_model().objects.create_user(username, username+'@example.com', 'StrongPass123!')
        return Alumni.objects.create(user=user, campus=campus, college=college,
                                     course='Sample Program', graduation_year=2024,
                                     gender='M',province='Negros Oriental',city='Dumaguete',address='Test')

    def test_anonymous_cannot_view(self):
        result = self.client.get(reverse('surveys:employability_report'))
        self.assertEqual(result.status_code, 302)

    def test_non_staff_cannot_view(self):
        self.client.force_login(self.visitor)
        result = self.client.get(reverse('surveys:employability_report'))
        self.assertEqual(result.status_code, 404)

    def test_counts_multiple_jobs_once_in_earliest_quarter(self):
        self.client.force_login(self.admin)
        result = self.client.get(reverse('surveys:employability_report'),
                                 {'cohort_year':2024,'report_year':2026,'as_of':'2026-09-30'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context['graduates'], 3)
        self.assertEqual(result.context['quarter_totals'], [1,0,1,0])
        self.assertEqual(result.context['total_hired'], 2)
        self.assertEqual(result.context['not_recorded'], 1)
        self.assertContains(result, 'Main campus subtotal')

    @override_settings(USE_TZ=False, TIME_ZONE='Asia/Manila')
    def test_employability_loads_with_project_naive_datetime_setting(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('surveys:employability_report'), {
            'cohort_year': 2024, 'report_year': 2026, 'as_of': '2026-09-30',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_hired'], 2)

    def test_exports_period_explicit_and_safe(self):
        self.client.force_login(self.admin)
        params={'cohort_year':2024,'report_year':2026,'as_of':'2026-09-30'}
        for filetype,extension in [('csv','csv'),('excel','xlsx'),('pdf','pdf')]:
            with self.subTest(filetype=filetype):
                response=self.client.get(reverse('surveys:employability_report'), {**params,'format':filetype})
                self.assertEqual(response.status_code, 200)
                self.assertIn('annual_2026',response['Content-Disposition'])
                self.assertIn(extension,response['Content-Disposition'])
        csv_result=self.client.get(reverse('surveys:employability_report'), {**params,'format':'csv'})
        self.assertIn(b'UNIVERSITY TOTAL',csv_result.content)
        self.assertNotIn(b'first@example.com',csv_result.content)

    def test_invalid_future_asof_rejected(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('surveys:employability_report'),
                                         {'as_of':'2999-01-01'}).status_code, 400)

    def test_public_forgot_password_is_not_login_required(self):
        response=self.client.get(reverse('account_reset_password'))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'email',status_code=200)
