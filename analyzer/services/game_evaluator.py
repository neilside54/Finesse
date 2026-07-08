"""
GameEvaluator - the single place that walks a game through Stockfish,
move by move.

Consolidates ALL Stockfish-dependent analysis into one pass:
  - Accuracy / resourcefulness / conversion  (was: skills_engine)
  - Blunder detection                        (was: stockfish_analyzer)
  - Per-piece accuracy                       (was: piece_engine)
  - Per-phase eval loss                      (was: phase_engine)
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any, Optional

import chess
import chess.engine
import chess.pgn


@dataclass(frozen=True)
class MoveEvaluation:
    """Position evaluation after a given move, from White's perspective (in pawns)."""

    ply: int
    color_moved: str  # "white" | "black"
    eval_after: float  # from White's perspective; mate = +-99.0
    best_move_uci: Optional[str] = None  # engine's top choice in UCI
    played_uci: Optional[str] = None  # UCI of the move actually played
    san: Optional[str] = None  # SAN notation of the move played
    piece_symbol: Optional[str] = None  # lowercase: "p", "n", "b", "r", "q", "k"
    is_user_move: bool = False
    is_best_move: bool = False  # played_uci == best_move_uci


@dataclass
class GameEvaluationTrace:
    """Full evaluation trace for a game - all metrics derived from this."""

    moves: list[MoveEvaluation] = field(default_factory=list)

    # --- Accuracy / centipawn loss ---

    def centipawn_loss_for(self, color: str) -> tuple[float, int]:
        total_loss = 0.0
        move_count = 0
        prev_eval_for_color = None

        for mv in self.moves:
            eval_c = mv.eval_after if color == "white" else -mv.eval_after
            if mv.color_moved == color:
                if prev_eval_for_color is not None:
                    loss = prev_eval_for_color - eval_c
                    if loss > 0:
                        total_loss += loss
                    move_count += 1
                prev_eval_for_color = eval_c
            else:
                prev_eval_for_color = eval_c

        return total_loss, move_count

    def accuracy_for(self, color: str) -> float:
        loss, move_count = self.centipawn_loss_for(color)
        if move_count == 0:
            return 100.0
        return max(0.0, min(100.0, round(100 - (loss / move_count) * 10, 1)))

    def eval_values_for(self, color: str) -> list[float]:
        return [
            (mv.eval_after if color == "white" else -mv.eval_after)
            for mv in self.moves
        ]

    # --- Blunder detection (replaces StockfishAnalyzer) ---

    def blunders_for(
        self, color: str, opponent_name: str = "Unknown", max_blunders: int = 5
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        blunders = []
        prev_eval = 0.0
        total_moves = len(self.moves)

        for mv in self.moves:
            eval_c = mv.eval_after if color == "white" else -mv.eval_after
            prev_c = prev_eval if color == "white" else -prev_eval

            if mv.color_moved == color and mv.is_user_move:
                drop = prev_c - eval_c
                if mv.ply > 2 and drop >= 1.5:
                    blunders.append({
                        "move_number": (mv.ply // 2) + 1,
                        "san": mv.san or "N/A",
                        "drop": round(drop, 2),
                        "severity": "Blunder" if drop > 3.0 else "Mistake",
                        "opponent": opponent_name,
                        "recommended_move": mv.best_move_uci or "N/A",
                    })

            prev_eval = mv.eval_after

        blunders.sort(key=lambda x: x["drop"], reverse=True)
        summary = {
            "total_moves": total_moves,
            "total_blunders": len(blunders),
            "critical_blunders": len([b for b in blunders if b["severity"] == "Blunder"]),
            "average_drop": (
                round(sum(b["drop"] for b in blunders) / len(blunders), 2)
                if blunders else 0.0
            ),
        }
        return blunders[:max_blunders], summary

    # --- Piece accuracy (replaces PieceEngine) ---

    def piece_accuracy_for(self, color: str) -> dict[str, dict[str, int]]:
        """
        Per-piece accuracy: how often the user played the engine's best move,
        broken down by piece type. Compares UCI strings directly to avoid
        parse failures.
        """
        piece_stats: dict[str, dict[str, int]] = {
            "P": {"correct": 0, "total": 0},
            "N": {"correct": 0, "total": 0},
            "B": {"correct": 0, "total": 0},
            "R": {"correct": 0, "total": 0},
            "Q": {"correct": 0, "total": 0},
            "K": {"correct": 0, "total": 0},
        }
        for mv in self.moves:
            if mv.color_moved != color or not mv.is_user_move:
                continue
            if not mv.piece_symbol:
                continue
            sym = mv.piece_symbol.upper()
            if sym not in piece_stats:
                continue
            piece_stats[sym]["total"] += 1
            # Direct UCI string comparison - no parse step needed
            if mv.played_uci and mv.best_move_uci and mv.played_uci == mv.best_move_uci:
                piece_stats[sym]["correct"] += 1
        return piece_stats

    # --- Phase analysis (replaces PhaseEngine) ---

    def phase_loss_for(self, color: str) -> dict[str, dict[str, float]]:
        """
        Average evaluation loss per game phase (opening/middlegame/endgame).
        """
        phases: dict[str, dict[str, float]] = {
            "opening": {"loss": 0.0, "count": 0},
            "middlegame": {"loss": 0.0, "count": 0},
            "endgame": {"loss": 0.0, "count": 0},
        }
        prev_eval = 0.0
        for mv in self.moves:
            eval_c = mv.eval_after if color == "white" else -mv.eval_after
            move_num = mv.ply + 1
            phase = (
                "opening" if move_num <= 15
                else "middlegame" if move_num <= 40
                else "endgame"
            )
            if mv.color_moved == color:
                loss = abs(prev_eval - eval_c)
                phases[phase]["loss"] += loss
                phases[phase]["count"] += 1
            prev_eval = eval_c
        return phases


class GameEvaluator:
    """Single Stockfish pass per game, building a GameEvaluationTrace."""

    def evaluate(
        self,
        pgn_string: str | None,
        engine: chess.engine.SimpleEngine,
        user_color: str = "white",
        time_limit: float = 0.05,
    ) -> GameEvaluationTrace | None:
        if not pgn_string:
            return None
        parsed_game = chess.pgn.read_game(io.StringIO(pgn_string))
        if parsed_game is None:
            return None

        board = parsed_game.board()
        limit = chess.engine.Limit(time=time_limit)
        trace = GameEvaluationTrace()
        user_color_bool = chess.WHITE if user_color == "white" else chess.BLACK

        for ply, node in enumerate(parsed_game.mainline()):
            move = node.move
            piece = board.piece_at(move.from_square)
            color_moved = "white" if board.turn == chess.WHITE else "black"
            is_user = piece is not None and piece.color == user_color_bool

            played_uci = move.uci()
            san = node.san()
            board.push(move)

            analysis = engine.analyse(board, limit)
            score_obj = analysis.get("score")
            pv = analysis.get("pv", [])

            if not score_obj or score_obj.white() is None:
                continue

            white_score = score_obj.white()
            eval_after = (
                (99.0 if white_score.mate() > 0 else -99.0)
                if white_score.is_mate()
                else white_score.score() / 100.0
            )

            best_uci = pv[0].uci() if pv else None
            piece_sym = chess.piece_symbol(piece.piece_type) if piece else None
            is_best = is_user and best_uci is not None and played_uci == best_uci

            trace.moves.append(MoveEvaluation(
                ply=ply,
                color_moved=color_moved,
                eval_after=eval_after,
                best_move_uci=best_uci,
                played_uci=played_uci,
                san=san,
                piece_symbol=piece_sym,
                is_user_move=is_user,
                is_best_move=is_best,
            ))

        return trace
