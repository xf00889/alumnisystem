"""Public access regression tests for member-only job board routes."""
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse


class MemberOnlyJobBoardTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_anonymous_job_board_requests_redirect_home_without_query_loop(self):
        routes = [
            reverse('jobs:job_list'),
            reverse('jobs:careers'),
            reverse('jobs:job_detail', kwargs={'slug': 'example-opening'}),
            reverse('jobs:get_job_details', kwargs={'job_id': 10}),
            reverse('jobs:check_job_application_eligibility', kwargs={'job_id': 10}),
        ]
        for route in routes:
            with self.subTest(route=route):
                request = self.factory.get(route)
                request.user = AnonymousUser()
                resolved = resolve(route)
                response = resolved.func(request, *resolved.args, **resolved.kwargs)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response['Location'], reverse('core:home'))

    def test_anonymous_modal_post_never_returns_job_data(self):
        url = reverse('jobs:get_job_details', kwargs={'job_id': 12})
        request = self.factory.post(url)
        request.user = AnonymousUser()
        resolved = resolve(url)
        response = resolved.func(request, *resolved.args, **resolved.kwargs)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('core:home'))
