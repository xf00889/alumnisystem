"""
Async task functions for global AI scoring.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model

from .ai_matching import get_ai_match_score
from .ai_global_sort import get_ai_profile_version, save_ai_score_result
from .models import JobPosting

logger = logging.getLogger(__name__)
User = get_user_model()


def _score_job_with_retry(user, job, max_retries: int = 2, backoff_seconds: float = 0.5) -> dict:
    attempt = 0
    while True:
        attempt += 1
        try:
            return get_ai_match_score(user, job)
        except Exception as exc:  # pragma: no cover - protective fallback
            if attempt > max_retries:
                logger.error(
                    "Async AI scoring exhausted retries for user=%s job=%s: %s",
                    user.id,
                    job.id,
                    exc,
                )
                return {
                    "error": True,
                    "reason": "AI scoring failed after retries.",
                    "score": None,
                    "strengths": [],
                    "gaps": [],
                }
            sleep_for = backoff_seconds * (2 ** (attempt - 1))
            time.sleep(sleep_for)


def process_user_ai_scores_for_job_ids(
    user_id: int,
    job_ids: List[int],
    profile_version: Optional[int] = None,
    max_retries: int = 2,
    backoff_seconds: float = 0.5,
) -> Dict[str, int]:
    """
    Background worker: score a specific set of jobs for a user.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"processed": 0, "ready": 0, "failed": 0}

    version = profile_version if profile_version is not None else get_ai_profile_version(user_id)
    jobs = {job.id: job for job in JobPosting.objects.filter(id__in=job_ids, is_active=True).exclude(slug="")}

    processed = 0
    ready = 0
    failed = 0

    for job_id in job_ids:
        job = jobs.get(job_id)
        if not job:
            continue

        score_data = _score_job_with_retry(
            user=user,
            job=job,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
        row = save_ai_score_result(
            user=user,
            job=job,
            profile_version=version,
            score_data=score_data,
        )

        processed += 1
        if row.status == row.Status.READY:
            ready += 1
        else:
            failed += 1

    return {"processed": processed, "ready": ready, "failed": failed}
