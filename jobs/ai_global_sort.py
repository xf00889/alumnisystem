"""
Services for global AI sorting across paginated job lists.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Dict, Iterable, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.db.models import Case, IntegerField, QuerySet, When
from django.utils import timezone

from .ai_matching import get_ai_match_score
from .models import JobPosting, UserJobAIScore

logger = logging.getLogger(__name__)


def get_ai_profile_version(user_id: int) -> int:
    return int(cache.get(f"ai_profile_version_{user_id}", 0) or 0)


def is_ai_score_stale(
    score_obj: Optional[UserJobAIScore],
    job: JobPosting,
    profile_version: int,
) -> bool:
    if not score_obj:
        return True
    if score_obj.status != UserJobAIScore.Status.READY:
        return True
    if score_obj.score is None:
        return True
    if score_obj.profile_version != profile_version:
        return True
    if not score_obj.computed_at:
        return True

    job_updated_at = getattr(job, "updated_at", None)
    if job_updated_at and score_obj.computed_at and job_updated_at > score_obj.computed_at:
        return True

    return False


def _normalize_list(value) -> List[str]:
    if isinstance(value, list):
        return value[:5]
    return []


def save_ai_score_result(
    *,
    user,
    job: JobPosting,
    profile_version: int,
    score_data: dict,
) -> UserJobAIScore:
    now = timezone.now()
    score_value = score_data.get("score")
    error_flag = bool(score_data.get("error", False))

    if error_flag or score_value is None:
        defaults = {
            "score": None,
            "reason": str(score_data.get("reason", ""))[:1000],
            "strengths_json": [],
            "gaps_json": [],
            "status": UserJobAIScore.Status.FAILED,
            "error_message": str(score_data.get("reason", "AI scoring failed."))[:1000],
            "profile_version": profile_version,
            "computed_at": now,
        }
    else:
        safe_score = max(0, min(100, int(score_value)))
        defaults = {
            "score": safe_score,
            "reason": str(score_data.get("reason", ""))[:1000],
            "strengths_json": _normalize_list(score_data.get("strengths")),
            "gaps_json": _normalize_list(score_data.get("gaps")),
            "status": UserJobAIScore.Status.READY,
            "error_message": "",
            "profile_version": profile_version,
            "computed_at": now,
        }

    row, _ = UserJobAIScore.objects.update_or_create(
        user=user,
        job=job,
        defaults=defaults,
    )
    return row


def mark_scores_pending(user, job_ids: Iterable[int], profile_version: int) -> None:
    now = timezone.now()
    for job_id in job_ids:
        UserJobAIScore.objects.update_or_create(
            user=user,
            job_id=job_id,
            defaults={
                "status": UserJobAIScore.Status.PENDING,
                "profile_version": profile_version,
                "error_message": "",
                "computed_at": now,
            },
        )


def get_stale_job_ids_for_jobs(user, jobs: List[JobPosting], profile_version: int) -> List[int]:
    if not jobs:
        return []

    job_ids = [j.id for j in jobs]
    existing = UserJobAIScore.objects.filter(user=user, job_id__in=job_ids)
    by_id = {row.job_id: row for row in existing}

    stale_ids: List[int] = []
    for job in jobs:
        if is_ai_score_stale(by_id.get(job.id), job, profile_version):
            stale_ids.append(job.id)
    return stale_ids


def compute_scores_for_job_ids(
    *,
    user,
    jobs_by_id: Dict[int, JobPosting],
    job_ids: List[int],
    profile_version: Optional[int] = None,
) -> int:
    if not job_ids:
        return 0

    version = profile_version if profile_version is not None else get_ai_profile_version(user.id)
    processed = 0

    mark_scores_pending(user, job_ids, version)

    for job_id in job_ids:
        job = jobs_by_id.get(job_id)
        if not job:
            continue

        try:
            score_data = get_ai_match_score(user, job)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error("AI score computation failed for user=%s job=%s: %s", user.id, job.id, exc)
            score_data = {
                "error": True,
                "reason": "AI matching service is temporarily unavailable.",
                "score": None,
                "strengths": [],
                "gaps": [],
            }

        save_ai_score_result(user=user, job=job, profile_version=version, score_data=score_data)
        processed += 1

    return processed


def rank_jobs_for_queryset(
    *,
    user,
    queryset: QuerySet,
    profile_version: Optional[int] = None,
    batch_size: Optional[int] = None,
    compute_batch: bool = True,
) -> dict:
    jobs = list(queryset.order_by("-posted_date"))
    total_count = len(jobs)
    if total_count == 0:
        return {
            "ordered_ids": [],
            "scored_count": 0,
            "pending_count": 0,
            "total_count": 0,
            "profile_version": profile_version if profile_version is not None else 0,
            "computed_now": 0,
        }

    version = profile_version if profile_version is not None else get_ai_profile_version(user.id)
    effective_batch = batch_size or getattr(settings, "AI_GLOBAL_SORT_BATCH_SIZE", 10)
    job_map = {job.id: job for job in jobs}

    stale_ids = get_stale_job_ids_for_jobs(user, jobs, version)
    pending_cutoff = timezone.now() - timedelta(
        minutes=max(1, int(getattr(settings, "AI_GLOBAL_PENDING_TIMEOUT_MINUTES", 5)))
    )
    pending_ids = set(
        UserJobAIScore.objects.filter(
            user=user,
            job_id__in=stale_ids,
            status=UserJobAIScore.Status.PENDING,
            profile_version=version,
            updated_at__gte=pending_cutoff,
        ).values_list("job_id", flat=True)
    )
    stale_ids = [job_id for job_id in stale_ids if job_id not in pending_ids]

    computed_now = 0
    if compute_batch and stale_ids:
        compute_ids = stale_ids[: max(1, int(effective_batch))]
        computed_now = compute_scores_for_job_ids(
            user=user,
            jobs_by_id=job_map,
            job_ids=compute_ids,
            profile_version=version,
        )

    score_rows = UserJobAIScore.objects.filter(
        user=user,
        job_id__in=job_map.keys(),
        status=UserJobAIScore.Status.READY,
    )
    fresh_scores: Dict[int, UserJobAIScore] = {}
    for row in score_rows:
        job = job_map.get(row.job_id)
        if job and not is_ai_score_stale(row, job, version):
            fresh_scores[row.job_id] = row

    scored_entries = []
    for job_id, row in fresh_scores.items():
        job = job_map[job_id]
        scored_entries.append((job_id, int(row.score or 0), job.posted_date))

    scored_entries.sort(key=lambda item: (item[1], item[2]), reverse=True)
    scored_ids = [item[0] for item in scored_entries]

    scored_set = set(scored_ids)
    unscored_ids = [job.id for job in jobs if job.id not in scored_set]
    ordered_ids = scored_ids + unscored_ids

    scored_count = len(scored_ids)
    pending_count = max(total_count - scored_count, 0)

    return {
        "ordered_ids": ordered_ids,
        "scored_count": scored_count,
        "pending_count": pending_count,
        "total_count": total_count,
        "profile_version": version,
        "computed_now": computed_now,
    }


def apply_ordered_ids(queryset: QuerySet, ordered_ids: List[int]) -> QuerySet:
    if not ordered_ids:
        return queryset

    ordering = Case(
        *[When(id=job_id, then=position) for position, job_id in enumerate(ordered_ids)],
        output_field=IntegerField(),
    )
    return queryset.filter(id__in=ordered_ids).order_by(ordering)
