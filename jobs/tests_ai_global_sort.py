import json
import sys
import types
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from jobs.ai_global_sort import is_ai_score_stale, rank_jobs_for_queryset
from jobs.models import JobPosting, UserJobAIScore

User = get_user_model()


class UserJobAIScoreModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ai_model_user",
            email="ai_model_user@example.com",
            password="testpass123",
        )
        self.job = JobPosting.objects.create(
            job_title="Backend Engineer",
            company_name="Acme",
            location="Dumaguete",
            job_type="FULL_TIME",
            job_description="Build APIs",
            posted_by=self.user,
        )

    def test_unique_user_job_constraint(self):
        UserJobAIScore.objects.create(
            user=self.user,
            job=self.job,
            status=UserJobAIScore.Status.READY,
            score=80,
            profile_version=1,
            computed_at=timezone.now(),
        )

        with self.assertRaises(IntegrityError):
            UserJobAIScore.objects.create(
                user=self.user,
                job=self.job,
                status=UserJobAIScore.Status.READY,
                score=70,
                profile_version=1,
                computed_at=timezone.now(),
            )

    def test_stale_detection_profile_version_and_job_update(self):
        now = timezone.now()
        JobPosting.objects.filter(id=self.job.id).update(updated_at=now - timedelta(minutes=5))
        self.job.refresh_from_db()

        row = UserJobAIScore.objects.create(
            user=self.user,
            job=self.job,
            status=UserJobAIScore.Status.READY,
            score=82,
            profile_version=5,
            computed_at=now,
        )

        self.assertFalse(is_ai_score_stale(row, self.job, 5))
        self.assertTrue(is_ai_score_stale(row, self.job, 6))

        JobPosting.objects.filter(id=self.job.id).update(updated_at=now + timedelta(minutes=1))
        self.job.refresh_from_db()
        self.assertTrue(is_ai_score_stale(row, self.job, 5))


class AIGlobalSortServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ai_service_user",
            email="ai_service_user@example.com",
            password="testpass123",
        )
        self.jobs = []
        for i in range(6):
            job = JobPosting.objects.create(
                job_title=f"Role {i}",
                company_name="Acme",
                location="Dumaguete",
                job_type="FULL_TIME",
                job_description="Role description",
                posted_by=self.user,
            )
            ts = timezone.now() - timedelta(hours=i)
            JobPosting.objects.filter(id=job.id).update(posted_date=ts, updated_at=ts)
            job.refresh_from_db()
            self.jobs.append(job)

    def test_partial_scoring_orders_scored_then_unscored(self):
        now = timezone.now()
        UserJobAIScore.objects.create(
            user=self.user,
            job=self.jobs[4],
            status=UserJobAIScore.Status.READY,
            score=95,
            profile_version=1,
            computed_at=now,
        )
        UserJobAIScore.objects.create(
            user=self.user,
            job=self.jobs[1],
            status=UserJobAIScore.Status.READY,
            score=60,
            profile_version=1,
            computed_at=now,
        )

        ranked = rank_jobs_for_queryset(
            user=self.user,
            queryset=JobPosting.objects.filter(id__in=[j.id for j in self.jobs]),
            profile_version=1,
            compute_batch=False,
        )

        scored_ids = [self.jobs[4].id, self.jobs[1].id]
        remaining = [job.id for job in sorted(self.jobs, key=lambda j: j.posted_date, reverse=True) if job.id not in set(scored_ids)]
        self.assertEqual(ranked["ordered_ids"], scored_ids + remaining)


class AIGlobalSortViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ai_view_user",
            email="ai_view_user@example.com",
            password="testpass123",
        )
        self.client.force_login(self.user)

        self.jobs = []
        for i in range(15):
            job = JobPosting.objects.create(
                job_title=f"Global Role {i}",
                company_name="Acme",
                location="Dumaguete",
                job_type="FULL_TIME",
                job_description="Role description",
                posted_by=self.user,
            )
            ts = timezone.now() - timedelta(hours=i)
            JobPosting.objects.filter(id=job.id).update(posted_date=ts, updated_at=ts)
            job.refresh_from_db()
            self.jobs.append(job)

    @patch("jobs.views._get_ai_sort_state", return_value=(False, 0))
    def test_job_list_without_ai_global_sort_keeps_default_order(self, _mock_ai_state):
        response = self.client.get(reverse("jobs:job_list"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["ai_global_mode"])

        expected = [job.id for job in sorted(self.jobs, key=lambda j: j.posted_date, reverse=True)[:10]]
        actual = [job.id for job in response.context["jobs"].object_list]
        self.assertEqual(actual, expected)

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    @patch("jobs.views.rank_jobs_for_queryset")
    def test_job_list_ai_global_applies_rank_before_pagination(self, mock_rank, _mock_ai_state):
        ordered_ids = [job.id for job in reversed(self.jobs)]
        mock_rank.return_value = {
            "ordered_ids": ordered_ids,
            "scored_count": 8,
            "pending_count": 7,
            "total_count": 15,
            "computed_now": 5,
        }

        response = self.client.get(f"{reverse('jobs:job_list')}?sort=ai_global")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["ai_global_mode"])

        first_page_ids = [job.id for job in response.context["jobs"].object_list]
        self.assertEqual(first_page_ids, ordered_ids[:10])

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    @patch("jobs.views.rank_jobs_for_queryset")
    def test_ai_global_progress_endpoint_returns_counts(self, mock_rank, _mock_ai_state):
        mock_rank.return_value = {
            "ordered_ids": [job.id for job in self.jobs],
            "scored_count": 5,
            "pending_count": 10,
            "total_count": 15,
            "computed_now": 3,
        }

        response = self.client.post(
            reverse("jobs:ai_global_progress"),
            data=json.dumps({"show_all": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["scored_count"], 5)
        self.assertEqual(payload["pending_count"], 10)
        self.assertEqual(payload["total_count"], 15)
        self.assertFalse(payload["complete"])

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    @patch("jobs.views.compute_scores_for_job_ids", return_value=3)
    @patch("jobs.views.get_stale_job_ids_for_jobs")
    @patch("jobs.views.importlib.util.find_spec", return_value=None)
    def test_ai_global_start_falls_back_to_sync_batch_when_queue_unavailable(
        self,
        _mock_find_spec,
        mock_stale_ids,
        _mock_compute_sync,
        _mock_ai_state,
    ):
        mock_stale_ids.return_value = [self.jobs[0].id, self.jobs[1].id, self.jobs[2].id]

        response = self.client.post(
            reverse("jobs:ai_global_start"),
            data=json.dumps({"show_all": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["processed_sync"], 3)
        self.assertFalse(payload["async_available"])

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    @patch("jobs.views.get_stale_job_ids_for_jobs")
    @patch("jobs.views.importlib.util.find_spec", return_value=object())
    def test_ai_global_start_skips_already_pending_and_queues_remaining(
        self,
        _mock_find_spec,
        mock_stale_ids,
        _mock_ai_state,
    ):
        mock_stale_ids.return_value = [self.jobs[0].id, self.jobs[1].id]
        UserJobAIScore.objects.create(
            user=self.user,
            job=self.jobs[0],
            status=UserJobAIScore.Status.PENDING,
            profile_version=1,
        )

        dummy_module = types.ModuleType("django_q.tasks")
        dummy_async_task = Mock()
        dummy_module.async_task = dummy_async_task
        dummy_package = types.ModuleType("django_q")
        dummy_package.tasks = dummy_module

        with patch.dict(sys.modules, {"django_q": dummy_package, "django_q.tasks": dummy_module}):
            response = self.client.post(
                reverse("jobs:ai_global_start"),
                data=json.dumps({"show_all": False}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["queued_jobs"], 1)
        self.assertTrue(payload["async_available"])
        dummy_async_task.assert_called_once()

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    def test_job_list_defaults_to_ai_global_when_sort_missing(self, _mock_ai_state):
        response = self.client.get(reverse("jobs:job_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["ai_global_mode"])
        self.assertEqual(response.context["current_sort"], "ai_global")

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    def test_job_list_supports_updated_sort(self, _mock_ai_state):
        first = self.jobs[-1]
        JobPosting.objects.filter(id=first.id).update(updated_at=timezone.now() + timedelta(days=1))

        response = self.client.get(f"{reverse('jobs:job_list')}?sort=updated")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["ai_global_mode"])
        self.assertEqual(response.context["current_sort"], "updated")
        first_page_ids = [job.id for job in response.context["jobs"].object_list]
        self.assertEqual(first_page_ids[0], first.id)

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    def test_job_list_query_filters_affect_result_set(self, _mock_ai_state):
        target = self.jobs[0]
        JobPosting.objects.filter(id=target.id).update(
            job_title="Unique Python Role",
            location="Dumaguete City",
            source_type="INTERNAL",
            job_type="FULL_TIME",
            salary_range="₱40,000 - ₱55,000",
            posted_date=timezone.now(),
        )

        response = self.client.get(
            reverse("jobs:job_list"),
            data={
                "q": "Unique Python",
                "location": "Dumaguete",
                "source_type": "INTERNAL",
                "job_type": "FULL_TIME",
                "posted_within": "7d",
                "salary_min": "30000",
                "sort": "latest",
            },
        )
        self.assertEqual(response.status_code, 200)
        ids = [job.id for job in response.context["jobs"].object_list]
        self.assertIn(target.id, ids)
        self.assertGreaterEqual(len(response.context["query_filter_chips"]), 1)

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    def test_job_list_partial_jobs_response(self, _mock_ai_state):
        response = self.client.get(
            reverse("jobs:job_list"),
            data={"partial": "jobs", "sort": "latest"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("jobs_html", payload)
        self.assertIn("filters_html", payload)

    @patch("jobs.views._get_ai_sort_state", return_value=(True, 1))
    def test_job_list_renders_mobile_actions_controls(self, _mock_ai_state):
        response = self.client.get(reverse("jobs:job_list"))
        self.assertContains(response, 'id="openFilterSheetBtn"')
        self.assertContains(response, 'id="mobileSortSelect"')
