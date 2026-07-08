"""
OpeningDetector — единая точка определения дебюта партии.

Не зависит от платформы (Chess.com / Lichess), не делает сетевых запросов.
Используется как инжектируемая зависимость в ChessAPIClient (или в любом
другом сервисе, которому нужно достоверное имя/ECO дебюта по PGN).

Стратегия определения (от дешёвой/точной к дорогой):
    1. Готовые данные платформы (если уже есть валидный name+eco — например, Lichess).
    2. Теги PGN [ECO] / [Opening].
    3. Тег [ECOUrl] (специфичен для Chess.com) — эвристически восстанавливаем
       читаемое имя из слага URL.
    4. Локальная ECO-книга: сопоставление по самому длинному совпадающему
       префиксу ходов партии (без сети).
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import chess
import chess.pgn

logger = logging.getLogger(__name__)

# Положите сюда полную базу, например, собранную из
# https://github.com/lichess-org/chess-openings (файлы a.tsv..e.tsv,
# объединённые в один файл со столбцами: eco, name, pgn).
DEFAULT_ECO_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "eco_openings.tsv"


@dataclass(frozen=True)
class OpeningInfo:
    """Унифицированный результат определения дебюта."""

    name: str
    eco: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "eco": self.eco}

    @property
    def is_known(self) -> bool:
        return self.eco != "???" and self.name != UNKNOWN_OPENING.name


UNKNOWN_OPENING = OpeningInfo(name="Unknown Opening", eco="???")


class _EcoTrieNode:
    __slots__ = ("children", "opening")

    def __init__(self) -> None:
        self.children: dict[str, "_EcoTrieNode"] = {}
        self.opening: Optional[OpeningInfo] = None


class EcoOpeningBook:
    """
    Локальная база дебютов в виде префиксного дерева по UCI-ходам.

    Позволяет находить дебют по самому длинному совпадающему префиксу
    реальной партии — без сетевых запросов и без хрупких регэкспов по PGN.
    Загрузка ленивая и происходит один раз (см. get_default_eco_book).
    """

    def __init__(self, tsv_path: Path = DEFAULT_ECO_DB_PATH) -> None:
        self._root = _EcoTrieNode()
        self._loaded = False
        self._tsv_path = tsv_path

    def lookup_by_moves(self, uci_moves: list[str]) -> Optional[OpeningInfo]:
        self._ensure_loaded()
        node = self._root
        best: Optional[OpeningInfo] = None
        for move in uci_moves:
            next_node = node.children.get(move)
            if next_node is None:
                break
            node = next_node
            if node.opening is not None:
                best = node.opening
        return best

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True  # ставим сразу, чтобы не пытаться грузить на каждый вызов

        if not self._tsv_path.exists():
            logger.warning(
                "ECO opening book not found at %s — move-based fallback отключён. "
                "Скачайте базу дебютов (например, lichess-org/chess-openings) и положите "
                "объединённый TSV туда же.",
                self._tsv_path,
            )
            return

        loaded_count = 0
        with self._tsv_path.open(encoding="utf-8") as f:
            header = f.readline()  # пропускаем заголовок столбцов
            for line_no, line in enumerate(f, start=2):
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 3:
                    logger.debug("Пропущена некорректная строка %d в %s", line_no, self._tsv_path)
                    continue

                eco, name, pgn_moves = parts[0].strip(), parts[1].strip(), parts[2].strip()
                uci_moves = self._movetext_to_uci(pgn_moves)
                if uci_moves:
                    self._insert(uci_moves, OpeningInfo(name=name, eco=eco))
                    loaded_count += 1

        logger.info("ECO opening book: загружено %d дебютных линий из %s", loaded_count, self._tsv_path)

    def _insert(self, uci_moves: list[str], opening: OpeningInfo) -> None:
        node = self._root
        for move in uci_moves:
            node = node.children.setdefault(move, _EcoTrieNode())
        # Более длинная (= более конкретная) линия имеет приоритет — поэтому
        # просто перезаписываем opening на каждой вставке книги в её собственный
        # терминальный узел; при поиске берём последний opening на пути, что
        # эквивалентно "самому длинному совпадению".
        node.opening = opening

    @staticmethod
    def _movetext_to_uci(pgn_moves: str) -> list[str]:
        """
        Конвертирует SAN-нотацию без заголовков ('1. e4 e5 2. Nf3 Nc6')
        в список UCI-ходов через python-chess (а не вручную регэкспами —
        это избавляет от багов с рокировками, взятиями на проходе и т.д.).
        """
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_moves))
        except Exception:
            logger.exception("Не удалось распарсить movetext ECO-книги: %r", pgn_moves)
            return []
        if game is None:
            return []
        return [move.uci() for move in game.mainline_moves()]


@lru_cache(maxsize=1)
def get_default_eco_book() -> EcoOpeningBook:
    """Синглтон базы дебютов — парсится один раз за жизнь процесса/воркера."""
    return EcoOpeningBook()


class OpeningDetector:
    """
    Сервис определения дебюта. Никакого I/O (HTTP), кроме чтения локального
    файла базы при первом обращении к EcoOpeningBook.
    """

    # Слаги Chess.com вида "Italian-Game-4...Nf6-5.OO" — отделяем "корневое"
    # имя дебюта от вариации, которая начинается с номера хода.
    _VARIATION_START_RE = re.compile(r"^\d+(\.{3})?\.?$")

    def __init__(self, eco_book: Optional[EcoOpeningBook] = None) -> None:
        self._eco_book = eco_book or get_default_eco_book()

    def detect(self, pgn: Optional[str], existing: Optional[dict] = None) -> OpeningInfo:
        """
        :param pgn: полный PGN партии (с заголовками или без).
        :param existing: то, что платформа уже отдала в поле "opening"
            (например, Lichess отдаёт валидные name/eco сразу — тогда
            смысла парсить PGN нет).
        """
        existing_info = self._from_existing(existing)
        if existing_info is not None:
            return existing_info

        if not pgn:
            return UNKNOWN_OPENING

        game = self._safe_parse_pgn(pgn)
        if game is None:
            return UNKNOWN_OPENING

        from_headers = self._from_headers(game)
        if from_headers is not None:
            return from_headers

        return self._from_moves(game)

    @staticmethod
    def _from_existing(existing: Optional[dict]) -> Optional[OpeningInfo]:
        if not existing:
            return None
        name = (existing.get("name") or "").strip()
        eco = (existing.get("eco") or "").strip()
        if name and name != UNKNOWN_OPENING.name and eco and eco != "???":
            return OpeningInfo(name=name, eco=eco)
        return None

    @staticmethod
    def _safe_parse_pgn(pgn: str) -> Optional[chess.pgn.Game]:
        try:
            return chess.pgn.read_game(io.StringIO(pgn))
        except Exception:
            logger.exception("Не удалось распарсить PGN для определения дебюта")
            return None

    def _from_headers(self, game: chess.pgn.Game) -> Optional[OpeningInfo]:
        headers = game.headers
        eco = headers.get("ECO", "").strip()
        name = headers.get("Opening", "").strip()

        if name and eco:
            return OpeningInfo(name=name, eco=eco)

        eco_url = headers.get("ECOUrl", "").strip()
        if eco_url:
            derived_name = self._name_from_eco_url(eco_url)
            if derived_name:
                return OpeningInfo(name=derived_name, eco=eco or "???")

        if eco:
            # Код есть, имени нет — лучше, чем "Unknown", но менее информативно.
            return OpeningInfo(name=f"ECO {eco}", eco=eco)

        return None

    def _from_moves(self, game: chess.pgn.Game) -> OpeningInfo:
        uci_moves = [move.uci() for move in game.mainline_moves()]
        if not uci_moves:
            return UNKNOWN_OPENING
        found = self._eco_book.lookup_by_moves(uci_moves)
        return found if found is not None else UNKNOWN_OPENING

    def _name_from_eco_url(self, eco_url: str) -> str:
        """
        Эвристика для Chess.com: ECOUrl выглядит как
        'https://www.chess.com/openings/Italian-Game-4...Nf6-5.OO'.
        Разбиваем по дефисам и отделяем номер хода — всё, что после него,
        считаем вариацией. ВНИМАНИЕ: это эвристика первой версии, её нужно
        проверить на реальных PGN из test_api.py — слаги Chess.com не всегда
        однородны (бывают без вариации, бывают с "..." внутри токена).
        """
        slug = eco_url.rstrip("/").rsplit("/", 1)[-1]
        tokens = slug.split("-")

        root_tokens: list[str] = []
        variation_tokens: list[str] = []
        in_variation = False

        for token in tokens:
            if not in_variation and self._VARIATION_START_RE.match(token):
                in_variation = True
            (variation_tokens if in_variation else root_tokens).append(token)

        name = " ".join(root_tokens).strip()
        if variation_tokens:
            name = f"{name}: {' '.join(variation_tokens)}" if name else " ".join(variation_tokens)
        return name