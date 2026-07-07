"""
ChessStatsEngine — overall profile statistics: breakdown by time control
(bullet/blitz/rapid/daily/...), win rate, and average rating for the user
and their opponents in each mode.

avg_peer_accuracy resolution order:
    1. Real data — RatingAccuracySample.benchmark_for(time_class, rating),
       averaged from actually-measured opponent accuracy samples collected
       by ChessSkillsEngine/GameEvaluator across analyzed games (any user's,
       not just this one — it's a community-wide running benchmark).
    2. Estimated fallback — RATING_ACCURACY_CURVE, a hand-picked
       rating -> expected-accuracy curve, used only while there isn't yet
       enough real data for that time_class/rating bucket.

Every mode's response includes "avg_peer_accuracy_source": "actual" or
"estimated" so the consumer (and the user) always knows which one they're
looking at — no value is presented as measured when it's actually a guess.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from analyzer.models import RatingAccuracySample
from analyzer.utils.visualizer import MetricVisualizer

# Curve points (rating -> expected accuracy, %), linearly interpolated between them.
# Hand-picked, NOT derived from measured data — see module docstring.
RATING_ACCURACY_CURVE: list[tuple[int, float]] = [
    (800, 50.0),
    (1000, 55.0),
    (1200, 60.0),
    (1400, 65.0),
    (1600, 70.0),
    (1800, 75.0),
    (2000, 80.0),
    (2200, 85.0),
    (2400, 90.0),
]

# How close a real-data sample's rating needs to be to the mode's average
# rating to be included in the benchmark average. See RatingAccuracySample.benchmark_for.
BENCHMARK_RATING_WINDOW = 100


class ChessStatsEngine:
    WIN_RATE_BENCHMARK = 50.0

    def analyze_profile(self, raw_games: list[dict[str, Any]], username: str) -> dict[str, Any]:
        if not raw_games:
            return {}

        overall_metrics = self._calculate_overall(raw_games)
        modes_metrics = self._calculate_modes(raw_games)

        modes_formatted = {
            mode: self._format_mode(data) for mode, data in modes_metrics.items()
        }

        return {
            "total_games": len(raw_games),
            "overall": self._format_overall(overall_metrics),
            "modes": modes_formatted,
            "verdict": self._generate_verdict(overall_metrics, modes_metrics),
        }

    # --- Raw metric collection -----------------------------------------------

    def _calculate_overall(self, raw_games: list[dict[str, Any]]) -> dict[str, Any]:
        wins = sum(1 for g in raw_games if g.get("user_result") == "win")
        losses = sum(1 for g in raw_games if g.get("user_result") == "loss")
        draws = sum(1 for g in raw_games if g.get("user_result") == "draw")
        total = len(raw_games)

        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round((wins / total) * 100, 1) if total else 0.0,
        }

    def _calculate_modes(self, raw_games: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for game in raw_games:
            mode = game.get("time_class") or "unknown"
            buckets[mode].append(game)

        modes_metrics: dict[str, dict[str, Any]] = {}
        for mode, games in buckets.items():
            total = len(games)
            wins = sum(1 for g in games if g.get("user_result") == "win")
            losses = sum(1 for g in games if g.get("user_result") == "loss")
            draws = sum(1 for g in games if g.get("user_result") == "draw")

            user_ratings = [g["user_rating"] for g in games if g.get("user_rating") is not None]
            peer_ratings = [g["opponent_rating"] for g in games if g.get("opponent_rating") is not None]

            avg_rating = round(sum(user_ratings) / len(user_ratings), 0) if user_ratings else 0.0
            avg_peer_rating = round(sum(peer_ratings) / len(peer_ratings), 0) if peer_ratings else 0.0

            avg_peer_accuracy, avg_peer_accuracy_source = self._resolve_peer_accuracy(mode, avg_rating)

            modes_metrics[mode] = {
                "total": total,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "win_rate": round((wins / total) * 100, 1) if total else 0.0,
                "avg_rating": avg_rating,
                "avg_peer_rating": avg_peer_rating,
                "avg_peer_accuracy": avg_peer_accuracy,
                "avg_peer_accuracy_source": avg_peer_accuracy_source,
            }

        return modes_metrics

    def _resolve_peer_accuracy(self, time_class: str, rating: float) -> tuple[float, str]:
        """
        Tries the real, measured community benchmark first; falls back to the
        estimated curve only if there isn't enough real data yet for this
        time_class/rating bucket.
        """
        if rating > 0:
            real_value = RatingAccuracySample.benchmark_for(
                time_class=time_class, rating=int(rating), rating_window=BENCHMARK_RATING_WINDOW
            )
            if real_value is not None:
                return real_value, "actual"

        return self._estimate_peer_accuracy(rating), "estimated"

    @staticmethod
    def _estimate_peer_accuracy(rating: float) -> float:
        """Linear interpolation over RATING_ACCURACY_CURVE. See module docstring."""
        if rating <= 0:
            return RATING_ACCURACY_CURVE[0][1]

        curve = RATING_ACCURACY_CURVE
        if rating <= curve[0][0]:
            return curve[0][1]
        if rating >= curve[-1][0]:
            return curve[-1][1]

        for (low_rating, low_acc), (high_rating, high_acc) in zip(curve, curve[1:]):
            if low_rating <= rating <= high_rating:
                span = high_rating - low_rating
                progress = (rating - low_rating) / span if span else 0
                return round(low_acc + (high_acc - low_acc) * progress, 1)

        return curve[-1][1]

    # --- Formatting ------------------------------------------------------------

    def _format_overall(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "total_games": metrics["total"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "draws": metrics["draws"],
            "win_rate": metrics["win_rate"],
            "visual": MetricVisualizer.get_bars(metrics["win_rate"], self.WIN_RATE_BENCHMARK, "default"),
        }

    def _format_mode(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "total_games": metrics["total"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "draws": metrics["draws"],
            "win_rate": metrics["win_rate"],
            "avg_rating": metrics["avg_rating"],
            "avg_peer_rating": metrics["avg_peer_rating"],
            "avg_peer_accuracy": metrics["avg_peer_accuracy"],
            "avg_peer_accuracy_source": metrics["avg_peer_accuracy_source"],
            "visual": MetricVisualizer.get_bars(metrics["win_rate"], self.WIN_RATE_BENCHMARK, "default"),
        }

    # --- Verdict -----------------------------------------------------------------

    def _generate_verdict(
        self, overall: dict[str, Any], modes: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Builds 3 verdicts: weak spot, strong spot, advice (same pattern as the other engines)."""
        messages: list[str] = []

        modes_with_volume = {m: d for m, d in modes.items() if d["total"] >= 3}

        if modes_with_volume:
            worst_mode, worst_data = min(modes_with_volume.items(), key=lambda kv: kv[1]["win_rate"])
            messages.append(
                f"In {worst_mode}, your win rate is only {worst_data['win_rate']}% "
                f"({worst_data['wins']}/{worst_data['total']}), which makes it the weakest area in your profile."
            )
        else:
            messages.append("There are not enough games in a single time control to identify a clear weak spot.")

        if modes_with_volume:
            best_mode, best_data = max(modes_with_volume.items(), key=lambda kv: kv[1]["win_rate"])
            messages.append(
                f"Your strongest time control is {best_mode} with a win rate of {best_data['win_rate']}%."
            )
        else:
            messages.append(f"Your overall win rate is {overall['win_rate']}%.")

        if overall["total"] < 20:
            messages.append("The game sample is small, so accuracy will improve as more history is collected.")
        elif modes_with_volume and len(modes_with_volume) > 1:
            messages.append(
                "Focus on one or two time controls to build more consistent results faster."
            )
        else:
            messages.append("Keep playing at your current pace — your results are stable.")

        return messages