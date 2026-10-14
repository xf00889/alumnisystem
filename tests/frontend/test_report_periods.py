"""Period boundary and filename regression checks, no Django needed.
python -m unittest discover -s tests/frontend -p 'test_report_periods.py' -v
"""
import unittest
from datetime import date
from core.report_periods import parse_report_period, export_download_name

NOW = date(2026, 10, 14)


class ReportPeriodTests(unittest.TestCase):
    def test_monthly_includes_leap_day(self):
        p = parse_report_period({'period':'monthly','year':'2024','month':'2'}, today=NOW)
        self.assertEqual((p.start,p.end), (date(2024,2,1),date(2024,2,29)))
        self.assertIn('monthly_2024-02', export_download_name('donations',p,'csv'))

    def test_quarters(self):
        for q, first, last in [(1,(1,1),(3,31)),(2,(4,1),(6,30)),(3,(7,1),(9,30)),(4,(10,1),(12,31))]:
            with self.subTest(q=q):
                p=parse_report_period({'period':'quarterly','year':'2026','quarter':str(q)}, today=NOW)
                self.assertEqual((p.start,p.end),(date(2026,*first),date(2026,*last)))
                self.assertIn(f'quarterly_2026-Q{q}',p.slug)

    def test_semiannual(self):
        p=parse_report_period({'period':'semi_annual','year':'2026','half':'1'},today=NOW)
        self.assertEqual((p.start,p.end),(date(2026,1,1),date(2026,6,30)))
        p=parse_report_period({'period':'semi_annual','year':'2026','half':'2'},today=NOW)
        self.assertEqual((p.start,p.end),(date(2026,7,1),date(2026,12,31)))

    def test_annual(self):
        p=parse_report_period({'period':'annual','year':'2025'},today=NOW)
        self.assertEqual((p.start,p.end),(date(2025,1,1),date(2025,12,31)))

    def test_one_day_and_custom(self):
        d=parse_report_period({'period':'day','day':'2026-10-14'},today=NOW)
        self.assertEqual((d.start,d.end),(NOW,NOW))
        self.assertEqual(d.slug,'one-day_2026-10-14')
        c=parse_report_period({'period':'custom','start_date':'2026-10-01','end_date':'2026-10-14'},today=NOW)
        self.assertIn('custom_2026-10-01_to_2026-10-14',c.slug)
        same=parse_report_period({'start_date':'2026-10-14','end_date':'2026-10-14'},today=NOW)
        self.assertEqual(same.slug,'one-day_2026-10-14')

    def test_bad_dates_rejected(self):
        for params in [{'period':'quarterly','quarter':'5'}, {'period':'custom','start_date':'2026-10-15','end_date':'2026-10-14'}, {'period':'day','day':'2026-02-31'}, {'period':'unknown'}]:
            with self.subTest(params=params), self.assertRaises(ValueError):
                parse_report_period(params,today=NOW)

    def test_all_time_omission_explicit(self):
        p=parse_report_period({},today=NOW)
        self.assertEqual(p.slug,'all-time')
        self.assertEqual(export_download_name('Alumni Directory',p,'pdf'),'norsu_alumni-directory_all-time.pdf')


if __name__ == '__main__':
    unittest.main()
