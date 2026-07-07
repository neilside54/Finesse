"""
ChessPieceEngine - per-piece accuracy analysis.

Now accepts pre-computed GameEvaluationTraces from the pipeline's single
Stockfish pass, rather than running its own independent engine calls.
"""

from analyzer.utils.visualizer import MetricVisualizer
from analyzer.services.game_evaluator import GameEvaluationTrace


class ChessPieceEngine:
    PEER_AVERAGES = {'P': 45.0, 'N': 42.0, 'B': 44.0, 'R': 46.0, 'Q': 48.0, 'K': 40.0}

    PIECE_NAMES_NOM = {'P': 'Pawns', 'N': 'Knights', 'B': 'Bishops', 'R': 'Rooks', 'Q': 'Queen', 'K': 'King'}
    PIECE_NAMES_INS = {'P': 'pawns', 'N': 'knights', 'B': 'bishops', 'R': 'rooks', 'Q': 'queen', 'K': 'king'}

    def analyze_from_traces(self, game_data):
        """
        Compute per-piece accuracy from pre-computed traces.
        game_data is a list of (raw_game_dict, GameEvaluationTrace|None) tuples.
        """
        piece_stats = {
            'P': {'correct': 0, 'total': 0}, 'N': {'correct': 0, 'total': 0},
            'B': {'correct': 0, 'total': 0}, 'R': {'correct': 0, 'total': 0},
            'Q': {'correct': 0, 'total': 0}, 'K': {'correct': 0, 'total': 0}
        }

        for game, trace in game_data:
            if trace is None or not trace.moves:
                continue
            user_color = game.get("user_color", "white")
            accuracy = trace.piece_accuracy_for(user_color)
            for sym, data in accuracy.items():
                piece_stats[sym]['correct'] += data['correct']
                piece_stats[sym]['total'] += data['total']

        final_report = self._format_results(piece_stats)
        final_report["verdict"] = self._generate_verdict(final_report)
        return final_report

    def _format_results(self, piece_stats):
        results = {}
        for p, d in piece_stats.items():
            if d['total'] > 0:
                accuracy = (d['correct'] / d['total']) * 100
                peer_val = self.PEER_AVERAGES.get(p, 45.0)
                results[p] = {
                    "raw": round(accuracy, 1),
                    "peer": peer_val,
                    "peer_source": "estimated",
                    "visual": MetricVisualizer.get_bars(accuracy, peer_val, metric_type="accuracy")
                }
            else:
                results[p] = {
                    "raw": 0.0,
                    "peer": self.PEER_AVERAGES.get(p, 45.0),
                    "peer_source": "estimated",
                    "visual": {"bars": 3, "status": "equal", "color": "yellow"}
                }
        return results

    def _generate_verdict(self, results):
        messages = []
        deltas = []
        for p, d in results.items():
            if p == "verdict":
                continue
            deltas.append({"symbol": p, "delta": d["raw"] - d["peer"], "raw": d["raw"]})
        deltas_sorted = sorted(deltas, key=lambda x: x["delta"])
        worst = deltas_sorted[0]
        best = deltas_sorted[-1]
        if worst["delta"] < -2.0:
            messages.append(f"Weakness found: your {self.PIECE_NAMES_NOM[worst['symbol']]} accuracy is {worst['raw']}%, below average.")
        else:
            messages.append("Your piece coordination is stable, with no major accuracy gaps.")
        messages.append(f"Your strongest piece performance is with {self.PIECE_NAMES_INS[best['symbol']]}. This is currently your most reliable asset.")
        advice_map = {
            'P': "Avoid weakening your pawn structure - doubled and isolated pawns become easy targets.",
            'N': "Knights are strongest on strong central squares. Avoid placing them on the edge of the board.",
            'B': "Bishops need open diagonals. Don't block your own long-range bishops with pawn chains.",
            'R': "Rooks excel on open or half-open files. Aim to place them on the 7th rank whenever possible.",
            'Q': "Avoid bringing the queen out too early - your opponent can gain tempo by attacking it.",
            'K': "King safety is your top priority. Do not delay castling in the middlegame."
        }
        messages.append(advice_map.get(worst['symbol'], "Review piece trajectories carefully to avoid blunders and improve coordination."))
        return messages
