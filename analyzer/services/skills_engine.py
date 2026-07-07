"""
ChessSkillsEngine calculates player skill metrics: accuracy, resourcefulness, and conversion.

Now accepts pre-computed GameEvaluationTraces from the pipeline's single Stockfish pass,
rather than running its own GameEvaluator pass. This eliminates redundant engine calls.
"""

from __future__ import annotations

from typing import Any

import chess.engine

from analyzer.services.game_evaluator import GameEvaluationTrace
from analyzer.utils.visualizer import MetricVisualizer


class ChessSkillsEngine:
    PEER_BENCHMARKS = {
        "accuracy": 65.0,
        "resourcefulness": 40.0,
        "conversion": 50.0,
    }

    def analyze_skills_from_traces(
        self,
        game_data: list[tuple[dict[str, Any], GameEvaluationTrace | None]],
        username: str,
    ) -> dict[str, Any]:
        """
        Compute skills from pre-computed traces (no Stockfish calls).
        game_data is a list of (raw_game_dict, trace) tuples.
        """
        total_centipawn_loss = 0.0
        total_user_moves = 0
        games_with_bad_position = 0
        saved_bad_positions = 0
        games_with_good_position = 0
        won_good_positions = 0
        peer_samples: list[dict[str, Any]] = []

        for game, trace in game_data:
            if trace is None or not trace.moves:
                continue

            user_color = game.get("user_color", "white")
            opponent_color = "black" if user_color == "white" else "white"
            user_result = game.get("user_result", "draw")

            user_loss, user_moves = trace.centipawn_loss_for(user_color)
            total_centipawn_loss += user_loss
            total_user_moves += user_moves

            opponent_accuracy = trace.accuracy_for(opponent_color)
            opponent_rating = game.get("opponent_rating")
            if opponent_rating:
                peer_samples.append({
                    "rating": opponent_rating,
                    "accuracy": opponent_accuracy,
                    "time_class": game.get("time_class") or "unknown",
                })

            user_perspective_evals = trace.eval_values_for(user_color)
            had_winning_advantage = any(ev >= 2.5 for ev in user_perspective_evals)
            had_losing_position = any(ev <= -2.5 for ev in user_perspective_evals)

            if had_losing_position:
                games_with_bad_position += 1
                if user_result in ("win", "draw"):
                    saved_bad_positions += 1

            if had_winning_advantage:
                games_with_good_position += 1
                if user_result == "win":
                    won_good_positions += 1

        accuracy = max(0.0, min(100.0, round(
            100 - ((total_centipawn_loss / total_user_moves if total_user_moves > 0 else 0) * 10), 1)))
        resourcefulness = round((saved_bad_positions / games_with_bad_position) * 100,
                                 1) if games_with_bad_position > 0 else 100.0
        conversion = round((won_good_positions / games_with_good_position) * 100,
                            1) if games_with_good_position > 0 else 100.0

        metrics = {"accuracy": accuracy, "resourcefulness": resourcefulness, "conversion": conversion}
        peer_accuracy_actual = (
            round(sum(s["accuracy"] for s in peer_samples) / len(peer_samples), 1)
            if peer_samples else None
        )

        results = self._format_results(metrics, peer_accuracy_actual)
        results["verdict"] = self._generate_verdict(results)
        results["peer_accuracy_samples"] = peer_samples
        results["peer_accuracy_actual"] = peer_accuracy_actual
        return results

    def _format_results(self, metrics, peer_accuracy_actual):
        formatted = {}
        for key, value in metrics.items():
            if key == "accuracy" and peer_accuracy_actual is not None:
                benchmark = peer_accuracy_actual
                source = "actual"
            else:
                benchmark = self.PEER_BENCHMARKS.get(key, 50.0)
                source = "estimated"
            formatted[key] = {
                "raw": value,
                "peer": benchmark,
                "peer_source": source,
                "visual": MetricVisualizer.get_bars(value, benchmark, "accuracy"),
            }
        return formatted

    def _generate_verdict(self, results):
        messages = []
        acc = results["accuracy"]["raw"]
        res = results["resourcefulness"]["raw"]
        conv = results["conversion"]["raw"]
        skills = [("Accuracy", acc), ("Resourcefulness", res), ("Conversion", conv)]
        skills.sort(key=lambda x: x[1])
        worst = skills[0]
        best = skills[-1]
        messages.append(f"Your weakest skill is {worst[0].lower()} ({worst[1]}%). This is the area that limits your improvement.")
        messages.append(f"At the same time, {best[0].lower()} is strong at {best[1]}%, above the benchmark.")
        if worst[0] == "Accuracy":
            messages.append("Spend more time calculating short tactical sequences - this will improve your overall accuracy.")
        elif worst[0] == "Resourcefulness":
            messages.append("Avoid resigning too quickly in difficult positions. Look for opponent mistakes until the end.")
        else:
            messages.append("Work on converting good positions into wins: a lead only matters if you can finish the game.")
        return messages
