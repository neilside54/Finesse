from celery import shared_task
from analyzer.services.chess_api import ChessAPIClient
from analyzer.services.stats_engine import ChessStatsEngine
import asyncio


@shared_task
def analyze_chess_profile_task(username, platform, limit):
    """Фоновая задача для скачивания и анализа партий"""
    api_client = ChessAPIClient()
    stats_engine = ChessStatsEngine()

    # Так как наш клиент асинхронный, а Celery синхронный — запускаем через event loop
    raw_games = asyncio.run(api_client.get_games(username=username, platform=platform, limit=limit))
    report = stats_engine.analyze_profile(raw_games, username=username)

    return report