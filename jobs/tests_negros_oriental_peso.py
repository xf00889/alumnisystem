"""Regression tests for public Negros Oriental PESO vacancy-category monitoring."""
import unittest
from unittest.mock import patch

from jobs.botasaurus_scrapers.negros_oriental_peso_scraper import (
    HOMEPAGE,
    _approved_url,
    public_vacancy_categories,
    provincial_vacancy_count,
    scrape_negros_oriental_peso,
)

HOME_HTML = '''
<h2>TOP VACANCIES FOR APPLICANTS</h2>
<ul>
<li><a href="/details.aspx?id=2118&amp;position=STAFF+NURSE&amp;t=vacancies">STAFF NURSE</a> (500)</li>
<li><a href="/details.aspx?id=8130&amp;position=PRODUCTION+WORKER&amp;t=vacancies">PRODUCTION WORKER</a> (2000)</li>
<li><a href="https://bad.example/details.aspx?id=3&amp;t=vacancies">EXTERNAL</a></li>
</ul>
<h2>TOP SKILLS FOR EMPLOYERS</h2>
<a href="/details.aspx?id=7&amp;t=skills">STAFF NURSE</a>
'''
DETAIL_HTML = '''
<h4>Available vacancies</h4>
<ul>
<li>MANILA CITY (1,500)</li>
<li><a href="#">NEGROS ORIENTAL PROVINCIAL PESO (72)</a></li>
<li>DUMAGUETE CITY (30)</li>
</ul>
'''


class PESOPublicVacancyParserTests(unittest.TestCase):
    def test_allowlist_rejects_external_urls_and_skills(self):
        self.assertTrue(_approved_url(HOMEPAGE))
        self.assertTrue(_approved_url('https://peis.philjobnet.gov.ph/details.aspx?id=1&t=vacancies'))
        for url in (
            'http://peis.philjobnet.gov.ph/',
            'https://peis.philjobnet.gov.ph.evil.org/details.aspx?id=1&t=vacancies',
            'https://peis.philjobnet.gov.ph/details.aspx?id=1&t=skills',
            'https://peis.philjobnet.gov.ph/protected/',
        ):
            self.assertFalse(_approved_url(url))

    def test_public_category_discovery_excludes_employer_skills(self):
        self.assertEqual([title for title, _ in public_vacancy_categories(HOME_HTML)],
                         ['STAFF NURSE', 'PRODUCTION WORKER'])

    def test_uses_only_provincial_office_count(self):
        self.assertEqual(provincial_vacancy_count(DETAIL_HTML), 72)
        self.assertEqual(provincial_vacancy_count('<li>DUMAGUETE CITY (30)</li>'), 0)

    def test_returns_leads_not_jobs_and_filters_keyword(self):
        with patch('jobs.botasaurus_scrapers.negros_oriental_peso_scraper._get_html', side_effect=[HOME_HTML, DETAIL_HTML]):
            result = scrape_negros_oriental_peso('nurse', 'Philippines')
        self.assertTrue(result['success'])
        self.assertEqual(result['source'], 'PESO_NEGROS_ORIENTAL')
        self.assertEqual(result['jobs'], [])
        self.assertEqual(result['total_found'], 0)
        self.assertFalse(result['publishable'])
        self.assertEqual(result['lead_count'], 1)
        self.assertEqual(result['vacancy_leads'][0]['vacancy_count'], 72)
        self.assertEqual(result['vacancy_leads'][0]['title'], 'STAFF NURSE')

    def test_failed_retrieval_does_not_fabricate_jobs(self):
        with patch('jobs.botasaurus_scrapers.negros_oriental_peso_scraper._get_html', side_effect=ValueError('bad redirect')):
            result = scrape_negros_oriental_peso('nurse', 'Negros Oriental')
        self.assertFalse(result['success'])
        self.assertEqual(result['jobs'], [])
        self.assertEqual(result['lead_count'], 0)


