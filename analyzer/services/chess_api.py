import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChessAPIError(Exception):
    """Базовое исключение для ошибок API."""
    pass


class ChessAPIClient:
    """
    Клиент для интеграции с публичными API Chess.com и Lichess.org.
    Возвращает унифицированные данные о партиях для последующего анализа.
    """

    CHESS_COM_BASE_URL = "https://api.chess.com/pub/player"
    LICHESS_BASE_URL = "https://lichess.org/api"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        # Обязательно укажи реальное название проекта и почту, чтобы не забанили
        self.headers = {
            "User-Agent": "ChessSlizer/1.0 (Contact: your_email@example.com)"
        }

    async def get_games(self, username: str, platform: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Основной метод для получения партий.
        """
        if platform.lower() == "chess.com":
            return await self._fetch_chess_com_games(username, limit)
        elif platform.lower() == "lichess":
            return await self._fetch_lichess_games(username, limit)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def _fetch_chess_com_games(self, username: str, limit: int) -> List[Dict[str, Any]]:
        """Получение партий с Chess.com."""
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            try:
                archives_res = await client.get(f"{self.CHESS_COM_BASE_URL}/{username}/games/archives")
                archives_res.raise_for_status()
                archives = archives_res.json().get("archives", [])

                if not archives:
                    return []

                all_games = []
                for archive_url in reversed(archives):
                    res = await client.get(archive_url)
                    if res.status_code == 200:
                        month_games = res.json().get("games", [])
                        all_games.extend(reversed(month_games))

                    if len(all_games) >= limit:
                        break

                return [self._format_chess_com_game(g, username) for g in all_games[:limit]]

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ChessAPIError(f"User {username} not found on Chess.com")
                raise ChessAPIError(f"Chess.com API error: {e}")
            except Exception as e:
                raise ChessAPIError(f"Unexpected error: {e}")

    async def _fetch_lichess_games(self, username: str, limit: int) -> List[Dict[str, Any]]:
        """Получение партий с Lichess через NDJSON API."""
        params = {
            "max": limit,
            "pgnInJson": "true",
            "clocks": "true",
            "evals": "false",
            "opening": "true"
        }
        headers = {**self.headers, "Accept": "application/x-ndjson"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.LICHESS_BASE_URL}/games/user/{username}"
                async with client.stream("GET", url, params=params, headers=headers) as response:
                    if response.status_code == 404:
                        raise ChessAPIError(f"User {username} not found on Lichess")
                    response.raise_for_status()

                    games = []
                    async for line in response.aiter_lines():
                        if line.strip():
                            import json
                            game_data = json.loads(line)
                            games.append(self._format_lichess_game(game_data, username))
                    return games

            except httpx.HTTPStatusError as e:
                raise ChessAPIError(f"Lichess API error: {e}")
            except Exception as e:
                raise ChessAPIError(f"Unexpected error: {e}")

    def _format_chess_com_game(self, game: Dict, username: str) -> Dict[str, Any]:
        """Приведение данных Chess.com к единому формату."""
        is_white = game["white"]["username"].lower() == username.lower()
        user_data = game["white"] if is_white else game["black"]
        opp_data = game["black"] if is_white else game["white"]

        return {
            "platform": "chess.com",
            "game_id": game.get("uuid"),
            "pgn": game.get("pgn"),
            "time_class": game.get("time_class"),
            "rated": game.get("rated", True),
            "user_rating": user_data.get("rating"),
            "opponent_rating": opp_data.get("rating"),
            "opponent_name": opp_data.get("username"),
            "user_result": user_data.get("result"),
            "played_at": datetime.fromtimestamp(game.get("end_time", 0)),
        }

    def _format_lichess_game(self, game: Dict, username: str) -> Dict[str, Any]:
        """Приведение данных Lichess к единому формату (с исправлением бага)."""
        white_player = game["players"].get("white", {})
        black_player = game["players"].get("black", {})

        white_name = white_player.get("user", {}).get("name", "").lower()
        is_white = white_name == username.lower()

        user_data = white_player if is_white else black_player
        opp_data = black_player if is_white else white_player

        return {
            "platform": "lichess",
            "game_id": game.get("id"),
            "pgn": game.get("pgn"),
            "time_class": game.get("speed"),
            "rated": game.get("rated", True),
            "user_rating": user_data.get("rating"),
            "opponent_rating": opp_data.get("rating"),
            "opponent_name": opp_data.get("user", {}).get("name", "AI"),
            "user_result": self._parse_lichess_result(game, is_white),
            "played_at": datetime.fromtimestamp(game.get("createdAt", 0) / 1000),
        }

    def _parse_lichess_result(self, game: Dict, is_white: bool) -> str:
        winner = game.get("winner")
        if not winner:
            return "draw"
        return "win" if (winner == "white" and is_white) or (winner == "black" and not is_white) else "loss"