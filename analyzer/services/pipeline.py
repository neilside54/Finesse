import asyncio
import inspect
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional

import chess.engine
from django.conf import settings

from analyzer.models import RatingAccuracySample
from analyzer.services.chess_api import ChessAPIClient
from analyzer.services.game_evaluator import GameEvaluator
from analyzer.services.opening_engine import ChessOpeningEngine
from analyzer.services.phase_engine import ChessPhaseEngine
from analyzer.services.piece_engine import ChessPieceEngine
from analyzer.services.skills_engine import ChessSkillsEngine
from analyzer.services.stats_engine import ChessStatsEngine


class ChessAnalysisPipeline:
    """Coordinates the full analysis flow with safer startup and graceful degradation."""

    def __init__(
        self,
        api_client: ChessAPIClient | None = None,
        stats_engine: ChessStatsEngine | None = None,
        opening_engine: ChessOpeningEngine | None = None,
        skills_engine: ChessSkillsEngine | None = None,
        phase_engine: ChessPhaseEngine | None = None,
        piece_engine: ChessPieceEngine | None = None,
        game_evaluator: GameEvaluator | None = None,
        engine_factory: Callable[[str], Any] | None = None,
        stockfish_path: str | os.PathLike[str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.api_client = api_client or ChessAPIClient()
        self.stats_engine = stats_engine or ChessStatsEngine()
        self.opening_engine = opening_engine or ChessOpeningEngine()
        self.skills_engine = skills_engine or ChessSkillsEngine()
        self.phase_engine = phase_engine or ChessPhaseEngine()
        self.piece_engine = piece_engine or ChessPieceEngine()
        self.game_evaluator = game_evaluator or GameEvaluator()
        self.engine_factory = engine_factory or self._default_engine_factory
        self.stockfish_path = stockfish_path
        self.logger = logger or logging.getLogger(__name__)

    def run_analysis(
        self,
        username: Optional[str],
        platform: str,
        limit: int,
        pgn_text: Optional[str] = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """
        Run the full analysis pipeline.

        If *progress_callback* is provided it is called periodically with a
        dict like ``{"phase": str, "current": int, "total": int, "message": str}``
        so that the caller (typically a Celery task) can broadcast real progress
        to the frontend.
        """
        def _emit(phase: str, current: int, total: int, message: str) -> None:
            if progress_callback:
                progress_callback({
                    "phase": phase,
                    "current": current,
                    "total": total,
                    "message": message,
                })

        _emit("fetching", 0, 1, "Fetching games from API...")

        try:
            games_result = self.api_client.get_games(
                username=username,
                platform=platform,
                limit=limit,
                pgn_text=pgn_text,
            )
            if inspect.isawaitable(games_result):
                raw_games = asyncio.run(games_result)
            else:
                raw_games = games_result
        except Exception as exc:
            return {"status": "error", "error": f"Failed to fetch games: {exc}"}

        if not raw_games:
            return {"error": "No games found"}

        _emit("fetching", 1, 1, f"Fetched {len(raw_games)} game(s). Preparing Stockfish...")

        engine_path = self._resolve_engine_path()
        if not engine_path:
            return {
                "status": "error",
                "error": (
                    "Stockfish engine not found. Expected one of: "
                    f"{', '.join(self._candidate_engine_paths())}"
                ),
            }

        errors: list[str] = []
        piece_telemetry: dict[str, Any] = {}
        blunders_report: list[dict[str, Any]] = []
        blunder_summaries: list[dict[str, Any]] = []
        skills_report: dict[str, Any] = {}
        phase_telemetry: dict[str, Any] = {}

        # ── SINGLE STOCKFISH PASS (with engine restart resilience) ────
        # Stockfish can crash (SIGSEGV) after many consecutive analyses.
        # We restart the engine every GAMES_PER_ENGINE games and also
        # catch "engine event loop dead" errors to respawn immediately.
        GAMES_PER_ENGINE = 50
        game_data: list[tuple[dict[str, Any], Any]] = []
        total = len(raw_games)
        _emit("analyzing", 0, total, f"Evaluating {total} game(s) with Stockfish...")

        engine = None
        games_on_current_engine = 0
        try:
            for idx, game in enumerate(raw_games, 1):
                # Restart engine if limit reached or previous one died
                if engine is None or games_on_current_engine >= GAMES_PER_ENGINE:
                    if engine is not None:
                        self.logger.info(
                            "Restarting Stockfish after %d games (preventive).",
                            games_on_current_engine,
                        )
                        try:
                            engine.close()
                        except Exception:
                            pass
                    try:
                        engine = self.engine_factory(engine_path)
                        games_on_current_engine = 0
                    except Exception as exc:
                        return {
                            "status": "error",
                            "error": f"Failed to launch Stockfish: {exc}",
                        }

                _emit("analyzing", idx, total, f"Analyzing game {idx}/{total}...")

                evaluated = False
                for attempt in range(2):  # max 2 attempts per game
                    try:
                        trace = self.game_evaluator.evaluate(
                            game.get("pgn"),
                            engine,
                            user_color=game.get("user_color", "white"),
                            time_limit=0.05,
                        )
                        game_data.append((game, trace))
                        games_on_current_engine += 1
                        evaluated = True
                        break
                    except Exception as exc:
                        exc_msg = str(exc)
                        is_dead = "dead" in exc_msg or "died" in exc_msg
                        if is_dead and attempt == 0:
                            # Engine died — restart and retry this game once
                            self.logger.warning(
                                "Engine died on game %d (%s), restarting...",
                                idx, exc_msg,
                            )
                            try:
                                engine.close()
                            except Exception:
                                pass
                            try:
                                engine = self.engine_factory(engine_path)
                                games_on_current_engine = 0
                            except Exception as restart_exc:
                                self.logger.error(
                                    "Engine restart failed: %s", restart_exc
                                )
                                break  # give up on remaining games
                        else:
                            self.logger.warning(
                                "Evaluation failed for %s: %s",
                                game.get("game_id"), exc_msg,
                            )
                            errors.append(
                                f"Evaluation failed for game {game.get('game_id')}: {exc_msg}"
                            )
                            game_data.append((game, None))
                            evaluated = True
                            break

                if not evaluated:
                    game_data.append((game, None))

            if engine is not None:
                try:
                    engine.close()
                except Exception:
                    pass

        except FileNotFoundError as exc:
            if engine is not None:
                try:
                    engine.close()
                except Exception:
                    pass
            return {"status": "error", "error": f"Stockfish engine not found: {exc}"}
        except OSError as exc:
            if engine is not None:
                try:
                    engine.close()
                except Exception:
                    pass
            return {"status": "error", "error": f"Failed to launch Stockfish: {exc}"}

        _emit("metrics", 0, 4, "Deriving piece accuracy...")

        # ── Derive all metrics from traces (no Stockfish calls) ──

        piece_telemetry = self._safe_call(
            "piece analysis",
            lambda: self.piece_engine.analyze_from_traces(game_data),
            errors,
            default={},
        )

        for game, trace in game_data:
            if trace is None:
                continue
            try:
                opponent_name = game.get("opponent_name", "Unknown")
                user_color = game.get("user_color", "white")
                top_blunders, summary = trace.blunders_for(
                    user_color, opponent_name=opponent_name
                )
                blunders_report.extend(top_blunders)
                blunder_summaries.append(summary)
            except Exception as exc:
                self.logger.warning(
                    "Blunder detection failed for %s: %s",
                    game.get("game_id"), exc,
                )
                errors.append(
                    f"Blunder detection failed for game {game.get('game_id')}: {exc}"
                )

        skills_report = self._safe_call(
            "skills analysis",
            lambda: self.skills_engine.analyze_skills_from_traces(
                game_data, username=username
            ),
            errors,
            default={},
        )
        self._persist_accuracy_samples(skills_report, platform, errors)

        phase_telemetry = self._safe_call(
            "phase analysis",
            lambda: self.phase_engine.analyze_from_traces(game_data),
            errors,
            default={},
        )

        # ── Transform engine dicts into frontend-compat metrics arrays ─
        piece_telemetry = self._normalize_piece_telemetry(piece_telemetry)
        phase_telemetry = self._normalize_phase_telemetry(phase_telemetry)

        _emit("stats", 0, 2, "Computing profile statistics...")

        base_report = self._safe_call(
            "profile statistics",
            lambda: self.stats_engine.analyze_profile(raw_games, username=username),
            errors,
            default={},
        )
        _emit("stats", 1, 2, "Analyzing openings...")

        opening_report = self._safe_call(
            "opening analysis",
            lambda: self.opening_engine.analyze_openings(raw_games, username=username),
            errors,
            default={},
        )

        if not isinstance(base_report, dict):
            base_report = {}
        if not isinstance(opening_report, dict):
            opening_report = {}
        if not isinstance(skills_report, dict):
            skills_report = {}
        if not isinstance(phase_telemetry, dict):
            phase_telemetry = {}
        if not isinstance(piece_telemetry, dict):
            piece_telemetry = {}

        # ── Assemble final report ─────────────────────────────────────
        snapshot = self._build_snapshot(
            skills_report, base_report, raw_games, len(raw_games)
        )
        highlights = self._build_highlights(
            skills_report, piece_telemetry, phase_telemetry, base_report
        )
        summary = self._build_summary(
            skills_report, base_report, highlights, raw_games
        )
        sections = self._build_analysis_sections(
            skills_report=skills_report,
            opening_report=opening_report,
            phase_telemetry=phase_telemetry,
            piece_telemetry=piece_telemetry,
            base_report=base_report,
        )

        status = "ok" if not errors else "partial"

        return {
            "status": status,
            "snapshot": snapshot,
            "summary": summary,
            "highlights": highlights,
            "sections": sections,
            "blunders": blunders_report,
            "blunder_summaries": blunder_summaries,
            "skills_telemetry": skills_report,
            "phase_telemetry": phase_telemetry,
            "piece_telemetry": piece_telemetry,
            "opening_stats": opening_report,
            "general_stats": base_report,
            "user_info": {
                "username": username,
                "platform": platform,
            },
            "warnings": [
                w for w in [
                    f"{len(errors)} game(s) had analysis errors." if errors else None,
                    "Game sample is small — accuracy will improve with more history."
                    if len(raw_games) < 20 else None,
                ]
                if w is not None
            ],
            "errors": errors,
        }

    # ── Snapshot ─────────────────────────────────────────────────────

    @staticmethod
    def _build_snapshot(
        skills_report: dict,
        base_report: dict,
        raw_games: list,
        total_games: int = 0,
    ) -> dict:
        skills = skills_report.get("overall", {})
        stats = base_report.get("overall", {})
        total = total_games or skills.get("total_games_analyzed", 0) or len(raw_games)
        peer_acc = skills.get("peer_accuracy")
        return {
            "accuracy": skills.get("avg_accuracy", 0),
            "win_rate": stats.get("win_rate", 0),
            "resourcefulness": skills.get("avg_resourcefulness", 0),
            "conversion": skills.get("avg_conversion", 0),
            "total_games": total,
            "peer_accuracy": peer_acc.get("value") if isinstance(peer_acc, dict) else peer_acc,
        }

    # ── Highlights ───────────────────────────────────────────────────

    @staticmethod
    def _build_highlights(
        skills_report: dict,
        piece_telemetry: dict,
        phase_telemetry: dict,
        base_report: dict,
    ) -> list[dict[str, Any]]:
        highlights: list[dict[str, Any]] = []

        # Accuracy highlight
        skills_overall = skills_report.get("overall", {})
        avg_acc = skills_overall.get("avg_accuracy")
        peer_acc = skills_overall.get("peer_accuracy")
        if avg_acc is not None:
            peer_val = peer_acc.get("value") if isinstance(peer_acc, dict) else peer_acc
            highlights.append({
                "title": "Overall Accuracy",
                "value": f"{avg_acc}%",
                "peer_average": f"{peer_val}%" if peer_val else None,
            })

        # Weakest piece
        pieces = piece_telemetry.get("metrics", [])
        if pieces:
            weakest = min(pieces, key=lambda m: m.get("value", 100))
            highlights.append({
                "title": f"Weakest Piece: {weakest.get('name', '?')}",
                "value": f"{weakest.get('value', 0)}%",
                "peer_average": f"{weakest.get('peer_average', 0)}%",
            })

        # Weakest phase
        phases = phase_telemetry.get("metrics", [])
        if phases:
            weakest_phase = min(phases, key=lambda m: m.get("value", 99))
            highlights.append({
                "title": f"Weakest Phase: {weakest_phase.get('name', '?')}",
                "value": f"{weakest_phase.get('value', 0)} pawns",
                "peer_average": f"{weakest_phase.get('peer_average', 0)} pawns",
            })

        # Win rate
        win_rate = base_report.get("overall", {}).get("win_rate")
        if win_rate is not None:
            highlights.append({
                "title": "Win Rate",
                "value": f"{win_rate}%",
            })

        return highlights

    # ── Summary ──────────────────────────────────────────────────────

    @staticmethod
    def _build_summary(
        skills_report: dict,
        base_report: dict,
        highlights: list,
        raw_games: list,
    ) -> dict:
        skills_overall = skills_report.get("overall", {})
        avg_acc = skills_overall.get("avg_accuracy", 0)
        peer_acc = skills_overall.get("peer_accuracy")
        peer_val = peer_acc.get("value") if isinstance(peer_acc, dict) else peer_acc
        peer_source = (
            peer_acc.get("source", "estimated")
            if isinstance(peer_acc, dict)
            else "estimated"
        )
        win_rate = base_report.get("overall", {}).get("win_rate", 0)

        # Determine priority area
        priority_label = None
        pieces = skills_report.get("by_piece", {})
        if pieces:
            weakest_piece = min(pieces, key=lambda k: pieces[k].get("accuracy", 100))
            priority_label = f"{weakest_piece} accuracy"

        if avg_acc and peer_val and avg_acc < peer_val - 3:
            summary_text = (
                f"Your average accuracy is {avg_acc}%, which is below the peer "
                f"benchmark of {peer_val}%. Focus on reducing blunders and "
                f"improving calculation in complex positions."
            )
        elif avg_acc and peer_val and avg_acc > peer_val + 3:
            summary_text = (
                f"Strong play — your {avg_acc}% accuracy exceeds the peer "
                f"average of {peer_val}%. Keep pushing your conversion rate "
                f"to turn more advantages into wins."
            )
        else:
            summary_text = (
                f"Solid performance at {avg_acc}% accuracy, right in line with "
                f"your peers at {peer_val}%. Your win rate is {win_rate}%. "
                f"Keep grinding to find consistent edges."
            )

        return {
            "summary_text": summary_text,
            "priority_label": priority_label,
            "peer_accuracy_source": peer_source,
        }

    # ── Sections ─────────────────────────────────────────────────────

    @staticmethod
    def _build_analysis_sections(
        skills_report: dict,
        opening_report: dict,
        phase_telemetry: dict,
        piece_telemetry: dict,
        base_report: dict,
    ) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []

        # Skills section
        if skills_report:
            metrics = []
            for key in ("avg_accuracy", "avg_resourcefulness", "avg_conversion"):
                label = key.replace("avg_", "").capitalize()
                value = skills_report.get("overall", {}).get(key, 0)
                peer = skills_report.get("overall", {}).get(f"peer_{key.replace('avg_', '')}")
                peer_val = peer.get("value") if isinstance(peer, dict) else peer
                peer_src = peer.get("source") if isinstance(peer, dict) else None
                metrics.append({
                    "name": label,
                    "value": value,
                    "peer_average": peer_val,
                    "peer_source": peer_src,
                })
            if metrics:
                sections.append({"id": "skills", "metrics": metrics})

        # Openings section
        if opening_report:
            sections.append({"id": "openings", **opening_report})

        # Game phases section
        if phase_telemetry:
            sections.append({"id": "game_phases", **phase_telemetry})

        # Piece accuracy section
        if piece_telemetry:
            sections.append({"id": "pieces", **piece_telemetry})

        # General stats section
        if base_report:
            sections.append({"id": "general_stats", **base_report})

        return sections

    # ── Telemetry normalisation ────────────────────────────────────

    @staticmethod
    def _normalize_piece_telemetry(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Transform piece engine output from ``{P: {...raw/peer...}, N: {...}, …}``
        to ``{metrics: [{name, value, peer_average, …}, …], verdict: …}`` so the
        frontend can iterate over a ``metrics`` array directly.
        """
        symbols = {"P", "N", "B", "R", "Q", "K"}
        metrics = [
            {
                "name": sym,
                "value": data.get("raw", 0),
                "peer_average": data.get("peer", 0),
                "peer_source": data.get("peer_source", "estimated"),
                "visual": data.get("visual", {}),
            }
            for sym, data in raw.items()
            if sym in symbols and isinstance(data, dict) and "raw" in data
        ]
        verdict = raw.get("verdict", [])
        result: dict[str, Any] = {"metrics": metrics}
        if verdict:
            result["verdict"] = verdict
        return result

    @staticmethod
    def _normalize_phase_telemetry(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Transform phase engine output from ``{opening: {...raw/peer...}, middlegame: …}``
        to ``{metrics: [{name, value, peer_average, …}, …], verdict: …}``.
        """
        phases = {"opening", "middlegame", "endgame"}
        metrics = [
            {
                "name": phase,
                "value": data.get("raw", 0),
                "peer_average": data.get("peer", 0),
                "peer_source": data.get("peer_source", "estimated"),
                "visual": data.get("visual", {}),
            }
            for phase, data in raw.items()
            if phase in phases and isinstance(data, dict) and "raw" in data
        ]
        verdict = raw.get("verdict", [])
        result: dict[str, Any] = {"metrics": metrics}
        if verdict:
            result["verdict"] = verdict
        return result

    # ── Accuracy persistence ─────────────────────────────────────────

    def _persist_accuracy_samples(
        self,
        skills_report: dict,
        platform: str,
        errors: list[str],
    ) -> None:
        """Save measured accuracy samples to the DB for community benchmarks."""
        for game_entry in skills_report.get("games", []):
            try:
                opp_rating = game_entry.get("opponent_rating")
                opp_accuracy = game_entry.get("opponent_accuracy")
                time_class = game_entry.get("time_class", "unknown")
                if opp_rating and opp_accuracy:
                    RatingAccuracySample.objects.create(
                        rating=opp_rating,
                        accuracy=opp_accuracy,
                        time_class=time_class,
                        platform=platform,
                    )
            except Exception as exc:
                errors.append(f"Failed to persist accuracy sample: {exc}")

    # ── Safe call wrapper ────────────────────────────────────────────

    def _safe_call(
        self,
        name: str,
        fn: Callable,
        errors: list[str],
        default: Any = None,
    ) -> Any:
        """Run *fn*, catching exceptions and appending to *errors*."""
        try:
            return fn()
        except Exception as exc:
            self.logger.warning("%s failed: %s", name, exc)
            errors.append(f"{name} failed: {exc}")
            return default

    # ── Engine path resolution ───────────────────────────────────────

    def _resolve_engine_path(self) -> Optional[str]:
        if self.stockfish_path and Path(self.stockfish_path).is_file():
            return str(self.stockfish_path)

        # Django settings
        sf_path = getattr(settings, "STOCKFISH_PATH", None)
        if sf_path and Path(sf_path).is_file():
            return str(sf_path)

        # Try candidate paths
        for candidate in self._candidate_engine_paths():
            if Path(candidate).is_file():
                return candidate

        return None

    @staticmethod
    def _candidate_engine_paths() -> list[str]:
        project_root = Path(__file__).resolve().parent.parent.parent
        return [
            str(project_root / "engines" / "stockfish"),
            str(project_root / "engines" / "stockfish.exe"),
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "/usr/games/stockfish",   # Debian package location
            "stockfish",
        ]

    # ── Default engine factory ───────────────────────────────────────

    @staticmethod
    def _default_engine_factory(engine_path: str):
        """Context manager that launches Stockfish and yields the engine."""
        return chess.engine.SimpleEngine.popen_uci(engine_path)
