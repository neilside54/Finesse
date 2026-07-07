"""
ChessPhaseEngine - per-phase eval loss analysis.

Now accepts pre-computed GameEvaluationTraces from the pipeline's single
Stockfish pass, rather than running its own independent engine calls.
"""

from analyzer.utils.visualizer import MetricVisualizer
from analyzer.services.game_evaluator import GameEvaluationTrace


class ChessPhaseEngine:
    PEER_BENCHMARKS = {
        "opening": 0.9,
        "middlegame": 1.1,
        "endgame": 1.3
    }
    PEER_SOURCE = "estimated"

    def analyze_from_traces(self, game_data):
        """
        Compute phase eval loss from pre-computed traces.
        game_data is a list of (raw_game_dict, GameEvaluationTrace|None) tuples.
        """
        phases = {
            "opening": {"loss": 0.0, "count": 0},
            "middlegame": {"loss": 0.0, "count": 0},
            "endgame": {"loss": 0.0, "count": 0}
        }

        for game, trace in game_data:
            if trace is None or not trace.moves:
                continue
            user_color = game.get("user_color", "white")
            game_phases = trace.phase_loss_for(user_color)
            for phase_name, data in game_phases.items():
                phases[phase_name]["loss"] += data["loss"]
                phases[phase_name]["count"] += data["count"]

        final_results = self._format_results(phases)
        final_results["verdict"] = self._generate_verdict(final_results)
        return final_results

    def _format_results(self, phases):
        results = {}
        for phase, data in phases.items():
            avg_loss = round(data["loss"] / data["count"], 2) if data["count"] > 0 else 0
            benchmark = self.PEER_BENCHMARKS.get(phase, 1.0)
            results[phase] = {
                "raw": avg_loss,
                "peer": benchmark,
                "peer_source": self.PEER_SOURCE,
                "visual": MetricVisualizer.get_bars(avg_loss, benchmark, metric_type="phase_loss", reverse=True)
            }
        return results

    def _generate_verdict(self, results):
        messages = []
        sorted_phases = sorted(
            [{"name": k, "loss": v["raw"]} for k, v in results.items() if isinstance(v, dict) and "raw" in v],
            key=lambda x: x["loss"], reverse=True
        )
        worst = sorted_phases[0]
        if worst["loss"] > self.PEER_BENCHMARKS.get(worst["name"], 1.0) + 0.3:
            messages.append(f"You are losing the most value during {worst['name']}. Focus on improving that phase.")
        else:
            messages.append("Your phase play is relatively balanced across the game.")
        best = sorted_phases[-1]
        messages.append(f"Your strongest phase is {best['name']}, which is your current comfort zone.")
        if worst["name"] == "endgame":
            messages.append("Work on endgame technique - this is the fastest way to improve your results.")
        elif worst["name"] == "opening":
            messages.append("Deepen your opening preparation for the lines you reach most often.")
        else:
            messages.append("Improve your middlegame planning by searching for more active ideas.")
        return messages
