# test_api.py
import asyncio
import json
from analyzer.services.chess_api import ChessAPIClient
from analyzer.services.stats_engine import ChessStatsEngine


async def test_full_pipeline():
    api_client = ChessAPIClient()
    stats_engine = ChessStatsEngine()

    username = "neilside"
    platform = "lichess"

    print(f"1. Запрашиваю последние партии для {username}...")
    try:
        # Скачиваем побольше игр (например, 15), чтобы посмотреть распределение
        raw_games = await api_client.get_games(username=username, platform=platform, limit=50)
        print(f"-> Успешно получено сырых партий: {len(raw_games)}")

        print("\n2. Запускаю шахматный анализатор...")
        report = stats_engine.analyze_profile(raw_games, username=username)

        print("\n=== ФИНАЛЬНЫЙ СГЕНЕРИРОВАННЫЙ JSON ОТЧЕТ ===")
        print(json.dumps(report, indent=4, ensure_ascii=False))
        print("============================================")

    except Exception as e:
        print(f"Ошибка в пайплайне: {e}")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())