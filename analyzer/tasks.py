import time as _time

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from analyzer.services.cache_keys import full_report_cache_key
from analyzer.services.chess_api import ChessAPIError
from analyzer.services.pipeline import ChessAnalysisPipeline


@shared_task(
    bind=True,
    autoretry_for=(ChessAPIError, ConnectionError, TimeoutError),
    retry_backoff=2,          # exponential: 2 s, 4 s, 8 s …
    retry_backoff_max=120,    # cap at 2 minutes
    retry_kwargs={"max_retries": 3},
)
def analyze_chess_profile_task(self, username, platform, limit, pgn_text=None, *args, **kwargs):
    """
    Celery task that runs the full analysis pipeline.

    Broadcasts real progress to the frontend via ``self.update_state()``.
    The frontend polls ``/api/task/<id>/`` and receives:
        {phase, current, total, message}  while running
        {status: "done", result: {...}}   on success
        {status: "failed", ...}           on failure
    """

    def _progress_callback(progress: dict) -> None:
        self.update_state(
            state="PROGRESS",
            meta=progress,
        )

    # Let exceptions propagate — Celery's autoretry_for handles retries
    # for transient errors (ChessAPIError, ConnectionError, TimeoutError).
    # Non-retryable failures (e.g. "No games found") are returned as
    # result dicts, not exceptions, so they won't trigger retries.
    pipeline = ChessAnalysisPipeline()
    result = pipeline.run_analysis(
        username=username,
        platform=platform,
        limit=limit,
        pgn_text=pgn_text,
        progress_callback=_progress_callback,
    )

    # Only cache usable results — a hard "error" status means nothing worth
    # reusing was produced (e.g. Stockfish missing, profile not found).
    # "ok"/"partial" reports are cached even with warnings, since partial
    # data is still cheaper to reuse than to recompute from scratch.
    if result.get("status") in ("ok", "partial"):
        cache_key = full_report_cache_key(platform, username, limit, pgn_text)
        ttl = getattr(settings, "STOCKFISH_CACHE_TTL_SECONDS", 3600 * 24)
        cache.set(cache_key, result, timeout=ttl)

    return result


@shared_task
def cleanup_expired_sessions():
    """Periodic task: delete Django sessions that have already expired.
    Runs via Celery Beat every hour (see CELERY_BEAT_SCHEDULE in settings)."""
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    expired = Session.objects.filter(expire_date__lt=timezone.now())
    count, _ = deleted = expired.delete()
    return {"deleted": count}