import json
from django.http import JsonResponse
from django.views import View
from django.urls import reverse
from analyzer.services.chess_api import ChessAPIClient, ChessAPIError
from analyzer.services.stats_engine import ChessStatsEngine
from analyzer.tasks import analyze_chess_profile_task
from celery.result import AsyncResult


# 1. Синхронный эндпоинт (Железный бэкап)
class ChessAnalyzeView(View):
    async def get(self, request, *args, **kwargs):
        username = request.GET.get("username")
        platform = request.GET.get("platform", "lichess")
        limit_raw = request.GET.get("limit", "50")

        if not username:
            return JsonResponse({"error": "Missing required parameter: username"}, status=400)

        try:
            limit = int(limit_raw)
        except ValueError:
            limit = 50

        api_client = ChessAPIClient()
        stats_engine = ChessStatsEngine()

        try:
            raw_games = await api_client.get_games(username=username, platform=platform, limit=limit)
            report = stats_engine.analyze_profile(raw_games, username=username)
            return JsonResponse(report, status=200, json_dumps_params={'ensure_ascii': False})
        except ChessAPIError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)


# 2. Асинхронный эндпоинт (Генерирует кликабельные ссылки для демонстрации)
class ChessAsyncAnalyzeView(View):
    def get(self, request, *args, **kwargs):
        username = request.GET.get("username")
        platform = request.GET.get("platform", "lichess")
        limit_raw = request.GET.get("limit", "50")

        if not username:
            return JsonResponse({"error": "Missing required parameter: username"}, status=400)

        try:
            limit = int(limit_raw)
        except ValueError:
            limit = 50

        # Запускаем фоновую задачу Celery
        task = analyze_chess_profile_task.delay(username, platform, limit)

        # Автоматически собираем ПОЛНУЮ живую ссылку для проверки статуса этой задачи
        status_url = request.build_absolute_uri(
            reverse('task-status', kwargs={'task_id': task.id})
        )

        # Автоматически собираем ПОЛНУЮ ссылку на синхронный обходной путь (бэкап)
        sync_fallback_url = request.build_absolute_uri(
            reverse('chess-analyze')
        ) + f"?username={username}&platform={platform}&limit={limit}"

        # Возвращаем красивый структурированный ответ
        return JsonResponse({
            "status": "processing",
            "task_id": task.id,
            "link_to_check_status": status_url,
            "link_to_sync_run_fallback": sync_fallback_url
        }, status=202)


# 3. Эндпоинт проверки статуса
class TaskStatusView(View):
    def get(self, request, task_id, *args, **kwargs):
        res = AsyncResult(task_id)
        if res.ready():
            return JsonResponse({
                "status": "done",
                "result": res.result
            }, json_dumps_params={'ensure_ascii': False})

        return JsonResponse({
            "status": "pending",
            "message": "Анализ выполняется воркером Celery в фоне. Обновите эту страницу через пару секунд."
        }, json_dumps_params={'ensure_ascii': False})