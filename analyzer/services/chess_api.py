import io
import json
import httpx
import asyncio
import chess.pgn
from typing import List, Dict, Any, Optional
from datetime import datetime

from analyzer.services.opening_detector import OpeningDetector


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

    # Retry configuration for rate-limited / transient API errors.
    MAX_RETRIES = 4
    BASE_BACKOFF = 1.0   # seconds; doubles each retry
    RETRYABLE_STATUS = {429, 500, 502, 503, 504}

    def __init__(self, timeout: int = 15, opening_detector: Optional[OpeningDetector] = None):
        self.timeout = timeout
        # Обязательно укажи реальное название проекта и почту, чтобы не забанили
        self.headers = {
            "User-Agent": "ChessSlizer/1.0 (Contact: your_email@example.com)"
        }
        # Инжектируется, а не создаётся внутри методов форматирования —
        # ChessAPIClient не должен знать, КАК определяется дебют, только
        # что есть зависимость, у которой можно его спросить.
        self._opening_detector = opening_detector or OpeningDetector()

    # ── Retry helper ────────────────────────────────────────────────

    @classmethod
    def _retryable(cls, exc: Exception) -> bool:
        """Return True if *exc* is a transient error worth retrying."""
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in cls.RETRYABLE_STATUS
        if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
            return True
        return False

    @classmethod
    def _backoff_seconds(cls, attempt: int) -> float:
        """Exponential backoff: 1 s, 2 s, 4 s, 8 s …"""
        return cls.BASE_BACKOFF * (2 ** attempt)

    @classmethod
    async def _retry_async(cls, fn, *args, **kwargs):
        """Call *fn* with retries on transient / rate-limit errors."""
        last_exc = None
        for attempt in range(cls.MAX_RETRIES):
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:
                if not cls._retryable(exc) or attempt == cls.MAX_RETRIES - 1:
                    raise
                last_exc = exc
                # Respect Retry-After header from 429 responses.
                retry_after = 0.0
                if isinstance(exc, httpx.HTTPStatusError):
                    try:
                        retry_after = float(
                            exc.response.headers.get("Retry-After", 0)
                        )
                    except (ValueError, TypeError):
                        retry_after = 0.0
                wait = max(retry_after, cls._backoff_seconds(attempt))
                await asyncio.sleep(wait)
        raise last_exc  # unreachable, but satisfies type checkers

    async def get_games(
        self,
        username: Optional[str],
        platform: str,
        limit: int = 100,
        pgn_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Основной метод для получения партий.
        """
        if pgn_text:
            return self.parse_pgn_games(pgn_text, username=username, platform=platform)

        if platform.lower() == "chess.com":
            return await self._fetch_chess_com_games(username or "", limit)
        elif platform.lower() == "lichess":
            return await self._fetch_lichess_games(username or "", limit)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def parse_pgn_games(
        self,
        pgn_text: str,
        username: Optional[str] = None,
        platform: str = "pgn",
    ) -> List[Dict[str, Any]]:
        """Parse one or more PGN games into the unified analysis format."""
        if not pgn_text:
            return []

        games: list[Dict[str, Any]] = []
        stream = io.StringIO(pgn_text)
        index = 0

        while True:
            game = chess.pgn.read_game(stream)
            if game is None:
                break

            index += 1
            games.append(self._format_pgn_game(game, username=username, platform=platform, index=index))

        return games

    def _format_pgn_game(
        self,
        game: chess.pgn.Game,
        username: Optional[str],
        platform: str,
        index: int,
    ) -> Dict[str, Any]:
        white_name = game.headers.get("White", "")
        black_name = game.headers.get("Black", "")
        normalized_username = username.lower() if username else ""

        if normalized_username and white_name.lower() == normalized_username:
            user_color = "white"
        elif normalized_username and black_name.lower() == normalized_username:
            user_color = "black"
        else:
            user_color = "white"

        result = game.headers.get("Result", "")
        if result == "1-0":
            raw_result = "white"
        elif result == "0-1":
            raw_result = "black"
        elif result == "1/2-1/2":
            raw_result = "draw"
        else:
            raw_result = ""

        if raw_result == "draw":
            user_result = "draw"
        elif raw_result == user_color:
            user_result = "win"
        else:
            user_result = "loss"

        user_rating = None
        opponent_rating = None
        if user_color == "white":
            user_rating = game.headers.get("WhiteElo")
            opponent_rating = game.headers.get("BlackElo")
        else:
            user_rating = game.headers.get("BlackElo")
            opponent_rating = game.headers.get("WhiteElo")

        try:
            user_rating = int(user_rating) if user_rating is not None else None
        except (ValueError, TypeError):
            user_rating = None

        try:
            opponent_rating = int(opponent_rating) if opponent_rating is not None else None
        except (ValueError, TypeError):
            opponent_rating = None

        played_at = None
        date_tag = game.headers.get("Date", "")
        if date_tag:
            parts = date_tag.split(".")
            if len(parts) == 3:
                try:
                    played_at = datetime(
                        year=int(parts[2]), month=int(parts[1]), day=int(parts[0])
                    )
                except ValueError:
                    played_at = None

        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        pgn_string = game.accept(exporter)

        return {
            "platform": platform,
            "game_id": game.headers.get("Site") or f"pgn-{index}",
            "pgn": pgn_string,
            "time_class": game.headers.get("TimeControl"),
            "rated": False,
            "user_rating": user_rating,
            "opponent_rating": opponent_rating,
            "opponent_name": black_name if user_color == "white" else white_name,
            "user_result": user_result,
            "user_color": user_color,
            "played_at": played_at,
            "opening": self._opening_detector.detect(pgn_string).as_dict(),
        }

    async def _fetch_chess_com_games(self, username: str, limit: int) -> List[Dict[str, Any]]:
        """Получение партий с Chess.com."""
        normalized_username = username.strip().lower()

        async def _do_fetch():
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                archives_res = await client.get(
                    f"{self.CHESS_COM_BASE_URL}/{normalized_username}/games/archives",
                    follow_redirects=True,
                )
                archives_res.raise_for_status()
                archives = archives_res.json().get("archives", [])

                if not archives:
                    return []

                all_games = []
                for archive_url in reversed(archives):
                    res = await client.get(archive_url, follow_redirects=True)
                    if res.status_code == 200:
                        month_games = res.json().get("games", [])
                        all_games.extend(reversed(month_games))

                    if len(all_games) >= limit:
                        break

                return [self._format_chess_com_game(g, normalized_username) for g in all_games[:limit]]

        try:
            return await self._retry_async(_do_fetch)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ChessAPIError(f"User {username} not found on Chess.com")
            raise ChessAPIError(f"Chess.com API error: {e}")
        except ChessAPIError:
            raise
        except Exception as e:
            raise ChessAPIError(f"Unexpected error: {e}")

    async def _fetch_lichess_games(self, username: str, limit: int) -> List[Dict[str, Any]]:
        """Получение партий с Lichess через NDJSON API."""
        bounded_limit = max(10, min(limit, 300))
        params = {
            "max": bounded_limit,
            "pgnInJson": "true",
            "clocks": "true",
            "evals": "false",
            "opening": "true"
        }
        headers = {**self.headers, "Accept": "application/x-ndjson"}

        async def _do_fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.LICHESS_BASE_URL}/games/user/{username}"
                async with client.stream("GET", url, params=params, headers=headers) as response:
                    if response.status_code == 404:
                        raise ChessAPIError(f"User {username} not found on Lichess")
                    response.raise_for_status()

                    games = []
                    async for line in response.aiter_lines():
                        if line.strip():
                            game_data = json.loads(line)
                            games.append(self._format_lichess_game(game_data, username))
                    return games

        try:
            return await self._retry_async(_do_fetch)
        except ChessAPIError:
            raise
        except httpx.HTTPStatusError as e:
            raise ChessAPIError(f"Lichess API error: {e}")
        except Exception as e:
            raise ChessAPIError(f"Unexpected error: {e}")

    def _format_chess_com_game(self, game: Dict, username: str) -> Dict[str, Any]:
        """Приведение данных Chess.com к единому формату."""
        is_white = game["white"]["username"].lower() == username.lower()
        user_data = game["white"] if is_white else game["black"]
        opp_data = game["black"] if is_white else game["white"]

        # Унифицируем результаты Chess.com под стандарт "win", "loss", "draw"
        raw_result = user_data.get("result")
        if raw_result == "win":
            user_result = "win"
        elif raw_result in ["draw", "stalemate", "insufficient", "repetition", "agreed"]:
            user_result = "draw"
        else:
            user_result = "loss"

        return {
            "platform": "chess.com",
            "game_id": game.get("uuid"),
            "pgn": game.get("pgn"),
            "time_class": game.get("time_class"),
            "rated": game.get("rated", True),
            "user_rating": user_data.get("rating"),
            "opponent_rating": opp_data.get("rating"),
            "opponent_name": opp_data.get("username"),
            "user_result": user_result,
            "user_color": "white" if is_white else "black",  # Сохраняем цвет
            "played_at": datetime.fromtimestamp(game.get("end_time", 0)),
            "opening": self._opening_detector.detect(game.get("pgn")).as_dict(),
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
            "user_color": "white" if is_white else "black",  # Передаем цвет!
            "played_at": datetime.fromtimestamp(game.get("createdAt", 0) / 1000),
            "opening": self._opening_detector.detect(
                game.get("pgn"), existing=game.get("opening")
            ).as_dict(),
        }

    def _parse_lichess_result(self, game: Dict, is_white: bool) -> str:
        winner = game.get("winner")
        if not winner:
            return "draw"
        return "win" if (winner == "white" and is_white) or (winner == "black" and not is_white) else "loss"