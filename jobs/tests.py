from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import JobPosting

User = get_user_model()

class JobPostingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.job = JobPosting.objects.create(
            job_title='Software Developer',
            company_name='Test Company',
            location='Test City',
            job_type='FULL_TIME',
            job_description='Test description',
            application_link='https://example.com/apply',
            posted_by=self.user
        )

    def test_job_creation(self):
        self.assertEqual(self.job.job_title, 'Software Developer')
        self.assertEqual(self.job.company_name, 'Test Company')
        self.assertTrue(self.job.slug)
        self.assertTrue(isinstance(self.job.posted_date, timezone.datetime))

    def test_job_str_representation(self):
        self.assertEqual(str(self.job), 'Software Developer at Test Company')

    def test_slug_generation(self):
        job = JobPosting.objects.create(
            job_title='Python Developer',
            company_name='Another Company',
            location='Test City',
            job_type='FULL_TIME',
            job_description='Test description',
            application_link='https://example.com/apply'
        )
        self.assertEqual(job.slug, 'python-developer-another-company')

class JobViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.job = JobPosting.objects.create(
            job_title='Software Developer',
            company_name='Test Company',
            location='Test City',
            job_type='FULL_TIME',
            job_description='Test description',
            application_link='https://example.com/apply',
            posted_by=self.user
        )

    def test_job_list_view(self):
        response = self.client.get(reverse('jobs:job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_list.html')
        self.assertContains(response, 'Software Developer')

    def test_job_detail_view(self):
        response = self.client.get(
            reverse('jobs:job_detail', kwargs={'slug': self.job.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_detail.html')
        self.assertContains(response, self.job.job_title)

    def test_post_job_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:post_job'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/post_job.html')

    def test_post_job_view_unauthenticated(self):
        response = self.client.get(reverse('jobs:post_job'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_create_job_posting(self):
        self.client.login(username='testuser', password='testpass123')
        job_data = {
            'job_title': 'Python Developer',
            'company_name': 'New Company',
            'location': 'Test City',
            'job_type': 'FULL_TIME',
            'job_description': 'Test description',
            'application_link': 'https://example.com/apply'
        }
        response = self.client.post(reverse('jobs:post_job'), job_data)
        self.assertEqual(response.status_code, 302)  # Redirects after successful creation
        self.assertTrue(
            JobPosting.objects.filter(job_title='Python Developer').exists()
        )

    def test_job_search(self):
        response = self.client.get(
            reverse('jobs:job_list'), {'q': 'Software'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Developer')

        response = self.client.get(
            reverse('jobs:job_list'), {'q': 'NonexistentJob'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Software Developer')
