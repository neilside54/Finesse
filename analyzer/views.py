import asyncio
import json
import re
import uuid

from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from celery.result import AsyncResult
from django_ratelimit.decorators import ratelimit

from analyzer.models import SavedAnalysis
from analyzer.services.cache_keys import full_report_cache_key, sync_report_cache_key
from analyzer.services.chess_api import ChessAPIClient, ChessAPIError
from analyzer.services.stats_engine import ChessStatsEngine
from analyzer.tasks import analyze_chess_profile_task

# ── Input validation constants ────────────────────────────────────────
MAX_LIMIT = 300
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")
MAX_PGN_LENGTH = 5 * 1024 * 1024  # 5 MB


def _extract_pgn_input_from_request(request):
    pgn_text = None

    if request.method == "GET":
        pgn_text = request.GET.get("pgn") or request.GET.get("pgn_text")
    else:
        pgn_text = request.POST.get("pgn") or request.POST.get("pgn_text")
        if not pgn_text and hasattr(request, "FILES") and request.FILES.get("pgn_file"):
            uploaded_file = request.FILES["pgn_file"]
            try:
                pgn_text = uploaded_file.read().decode("utf-8")
            except Exception:
                pgn_text = uploaded_file.read().decode("latin-1")

    if not pgn_text and request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            pgn_text = payload.get("pgn") or payload.get("pgn_text")
        except Exception:
            pgn_text = None

    return pgn_text


def _validate_inputs(username, platform, limit, pgn_text):
    """
    Validate and normalise request parameters. Returns (username, platform,
    limit, pgn_text, error_response) — *error_response* is a
    ``JsonResponse`` on failure, ``None`` on success.
    """
    # --- limit -------------------------------------------------------
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT

    # --- username (only validated when present) -----------------------
    if username:
        username = username.strip()
        if not USERNAME_RE.match(username):
            return (
                username,
                platform,
                limit,
                pgn_text,
                JsonResponse(
                    {
                        "error": (
                            "Invalid username. Use 1–50 alphanumeric "
                            "characters, hyphens, or underscores."
                        )
                    },
                    status=400,
                ),
            )

    # --- PGN length --------------------------------------------------
    if pgn_text and len(pgn_text.encode("utf-8")) > MAX_PGN_LENGTH:
        return (
            username,
            platform,
            limit,
            pgn_text,
            JsonResponse(
                {
                    "error": (
                        f"PGN data too large ({len(pgn_text)} chars). "
                        f"Maximum allowed is {MAX_PGN_LENGTH:,} bytes."
                    )
                },
                status=400,
            ),
        )

    return username, platform, limit, pgn_text, None


def _parse_request_params(request, default_platform: str, default_limit: str = "100"):
    """
    Shared GET/POST/JSON-body parameter extraction, used by both the sync
    and async analyze views to avoid duplicating the same parsing logic
    in four separate methods.
    """
    payload = None
    if request.method == "POST" and request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            payload = {}

    username = (payload.get("username") if payload else None) or request.POST.get("username") or request.GET.get("username")
    platform = (payload.get("platform") if payload else None) or request.POST.get("platform") or request.GET.get("platform", default_platform)
    limit_raw = (payload.get("limit") if payload else None) or request.POST.get("limit") or request.GET.get("limit", default_limit)
    pgn_text = _extract_pgn_input_from_request(request)

    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        limit = int(default_limit)

    if pgn_text:
        platform = "pgn"

    return username, platform, limit, pgn_text


# 0. Frontend page (SPA catch-all)
import os
from django.http import FileResponse

_VITE_INDEX = os.path.join(settings.BASE_DIR, 'staticfiles', 'index.html')


class FrontendView(View):
    """Serve the Vite SPA index.html for all non-API routes.

    In development the Vite dev server on :5173 handles this.
    In Docker / production the built SPA lives in staticfiles/index.html
    and Django serves it as a catch-all so react-router can handle
    client-side routing.
    """

    def get(self, request, *args, **kwargs):
        if os.path.isfile(_VITE_INDEX):
            # Don't use 'with' here — gunicorn's sendfile reads the file
            # asynchronously, and the context manager would close it early.
            return FileResponse(open(_VITE_INDEX, 'rb'), content_type='text/html')
        # Fallback to the legacy Django template during local dev
        return TemplateView.as_view(template_name='analyzer/index.html')(request, *args, **kwargs)


# 1. Synchronous endpoint (hard fallback — stats only, no Stockfish)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='30/m', method=['GET', 'POST'], block=True), name='dispatch')
class ChessAnalyzeView(View):
    def _handle(self, request, default_platform: str):
        username, platform, limit, pgn_text = _parse_request_params(request, default_platform)

        username, platform, limit, pgn_text, err = _validate_inputs(
            username, platform, limit, pgn_text,
        )
        if err is not None:
            return err

        if not username and not pgn_text:
            return JsonResponse({"error": "Missing required parameter: username or PGN data"}, status=400)

        cache_key = sync_report_cache_key(platform, username, limit, pgn_text)
        cached_report = cache.get(cache_key)
        if cached_report is not None:
            return JsonResponse(
                {**cached_report, "cached": True}, status=200, json_dumps_params={'ensure_ascii': False}
            )

        api_client = ChessAPIClient()
        stats_engine = ChessStatsEngine()

        try:
            raw_games = api_client.get_games(
                username=username,
                platform=platform,
                limit=limit,
                pgn_text=pgn_text,
            )
            if asyncio.iscoroutine(raw_games):
                raw_games = asyncio.run(raw_games)
            report = stats_engine.analyze_profile(raw_games, username=username or "PGN User")
            ttl = getattr(settings, "REPORT_CACHE_TTL_SECONDS", 3600)
            cache.set(cache_key, report, timeout=ttl)
            return JsonResponse({**report, "cached": False}, status=200, json_dumps_params={'ensure_ascii': False})
        except ChessAPIError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    def get(self, request, *args, **kwargs):
        return self._handle(request, default_platform="lichess")

    def post(self, request, *args, **kwargs):
        return self._handle(request, default_platform="pgn")


# 2. Async endpoint (Celery-backed full report, with Stockfish analysis)
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='10/m', method=['GET', 'POST'], block=True), name='dispatch')
class ChessAsyncAnalyzeView(View):
    def _handle(self, request, default_platform: str):
        username, platform, limit, pgn_text = _parse_request_params(request, default_platform)

        username, platform, limit, pgn_text, err = _validate_inputs(
            username, platform, limit, pgn_text,
        )
        if err is not None:
            return err

        if not username and not pgn_text:
            return JsonResponse({"error": "Missing required parameter: username or PGN data"}, status=400)

        # If a full report for this exact subject/platform/limit is already
        # cached, skip queueing a new Celery task entirely — this avoids
        # re-running Stockfish and re-fetching games for repeat lookups.
        cache_key = full_report_cache_key(platform, username, limit, pgn_text)
        cached_report = cache.get(cache_key)
        if cached_report is not None:
            # Generate a synthetic task_id so the frontend can route to the
            # results page.  Store under a known key so TaskStatusView can
            # find it without querying Celery.
            synthetic_id = f"cached-{uuid.uuid4().hex[:12]}"
            cache.set(
                f"task_result:{synthetic_id}",
                cached_report,
                timeout=getattr(settings, "STOCKFISH_CACHE_TTL_SECONDS", 3600 * 24),
            )
            return JsonResponse(
                {"status": "done", "result": cached_report, "task_id": synthetic_id, "cached": True},
                status=200,
                json_dumps_params={'ensure_ascii': False},
            )

        task = analyze_chess_profile_task.delay(username, platform, limit, pgn_text)

        status_url = request.build_absolute_uri(
            reverse('task-status', kwargs={'task_id': task.id})
        )
        sync_fallback_url = request.build_absolute_uri(
            reverse('chess-analyze'))
        if username:
            sync_fallback_url += f"?username={username}&platform={platform}&limit={limit}"

        return JsonResponse({
            "status": "processing",
            "task_id": task.id,
            "link_to_check_status": status_url,
            "link_to_sync_run_fallback": sync_fallback_url,
        }, status=202)

    def get(self, request, *args, **kwargs):
        return self._handle(request, default_platform="lichess")

    def post(self, request, *args, **kwargs):
        return self._handle(request, default_platform="pgn")


class InputOptionsView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "input_modes": [
                    {
                        "mode": "nickname",
                        "label": "Search by username",
                        "platforms": ["lichess", "chess.com"],
                        "description": "Analyze a public profile from Lichess or Chess.com by username.",
                    },
                    {
                        "mode": "pgn",
                        "label": "Upload PGN file",
                        "file_input": True,
                        "description": "Upload a local PGN file or use drag-and-drop for analysis.",
                    },
                ]
            },
            json_dumps_params={"ensure_ascii": False},
        )


# ── Saved analyses ──────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class SaveAnalysisView(View):
    """Persist a completed analysis to the logged-in user's library."""

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"error": "You must be logged in to save analyses."},
                status=401,
            )

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        task_id = payload.get("task_id", "").strip()
        if not task_id:
            return JsonResponse({"error": "task_id is required."}, status=400)

        report = payload.get("report", {})
        if not report:
            return JsonResponse({"error": "report data is required."}, status=400)

        user_info = report.get("user_info", {})
        subject = (
            user_info.get("username") or payload.get("subject") or "PGN Upload"
        )
        platform = user_info.get("platform") or payload.get("platform") or "unknown"
        total_games = (
            report.get("snapshot", {}).get("total_games")
            or report.get("total_games", 0)
        )

        saved, _ = SavedAnalysis.objects.update_or_create(
            user=request.user,
            task_id=task_id,
            defaults={
                "platform": platform,
                "subject": subject,
                "total_games": total_games,
                "report": report,
            },
        )

        return JsonResponse({
            "saved": True,
            "id": saved.id,
            "message": "Analysis saved to your library.",
        })


class SavedAnalysesView(View):
    """List the logged-in user's saved analyses."""

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        qs = SavedAnalysis.objects.filter(user=request.user).order_by("-created_at")[:50]
        items = [
            {
                "id": s.id,
                "task_id": s.task_id,
                "subject": s.subject,
                "platform": s.platform,
                "total_games": s.total_games,
                "created_at": s.created_at.isoformat(),
            }
            for s in qs
        ]
        return JsonResponse({"analyses": items})


class SavedAnalysisDetailView(View):
    """Retrieve or delete a single saved analysis by its database id."""

    def get(self, request, analysis_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        try:
            saved = SavedAnalysis.objects.get(id=analysis_id, user=request.user)
        except SavedAnalysis.DoesNotExist:
            return JsonResponse({"error": "Analysis not found."}, status=404)

        return JsonResponse({
            "id": saved.id,
            "task_id": saved.task_id,
            "subject": saved.subject,
            "platform": saved.platform,
            "total_games": saved.total_games,
            "report": saved.report,
            "created_at": saved.created_at.isoformat(),
        })

    def delete(self, request, analysis_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        try:
            saved = SavedAnalysis.objects.get(id=analysis_id, user=request.user)
        except SavedAnalysis.DoesNotExist:
            return JsonResponse({"error": "Analysis not found."}, status=404)

        saved.delete()
        return JsonResponse({"deleted": True})


# 3. Task status endpoint
class TaskStatusView(View):
    def get(self, request, task_id, *args, **kwargs):
        # First, check if this is a cached result (synthetic task_id from
        # ChessAsyncAnalyzeView cache-hit path).
        cached = cache.get(f"task_result:{task_id}")
        if cached is not None:
            return JsonResponse({
                "status": "done",
                "result": cached,
            }, json_dumps_params={'ensure_ascii': False})

        res = AsyncResult(task_id)

        if res.ready():
            # If the task failed
            if res.failed():
                return JsonResponse({
                    "status": "failed",
                    "error": "A Celery worker error occurred.",
                    "details": str(res.result)
                }, json_dumps_params={'ensure_ascii': False})

            # If the task completed successfully
            return JsonResponse({
                "status": "done",
                "result": res.result
            }, json_dumps_params={'ensure_ascii': False})

        # If the task is in PROGRESS state — return real pipeline progress
        if res.state == "PROGRESS":
            meta = res.info or {}
            return JsonResponse({
                "status": "processing",
                "phase": meta.get("phase", "analyzing"),
                "current": meta.get("current", 0),
                "total": meta.get("total", 0),
                "message": meta.get("message", "Analyzing..."),
            }, json_dumps_params={'ensure_ascii': False})

        # If the task is still pending/queued
        return JsonResponse({
            "status": "pending",
            "phase": "pending",
            "current": 0,
            "total": 0,
            "message": "Waiting for a worker to pick up the task..."
        }, json_dumps_params={'ensure_ascii': False})