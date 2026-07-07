from analyzer.utils.visualizer import MetricVisualizer


class ChessTimeEngine:
    # Reference points (estimated, not measured — see module-level note below):
    # A typical player gets into time trouble in under 20% of games.
    # A typical player makes fewer than 2 panic moves per game on average.
    # There's currently no measured population data for time-management
    # metrics (unlike accuracy, which has GameEvaluator-derived real samples
    # via RatingAccuracySample) — so these stay labeled "estimated" until
    # an equivalent measured data source exists for panic rate.
    PEER_BENCHMARKS = {
        "panic_rate": 20.0,
        "avg_panic_moves": 2.0
    }
    PEER_SOURCE = "estimated"

    def analyze_time(self, raw_games, username):
        total_games = len(raw_games)
        if total_games == 0: return {}

        # 1. Collect raw metrics
        metrics = self._calculate_raw_metrics(raw_games, total_games)

        # 2. Format results
        results = self._format_results(metrics)

        # 3. Generate 3 verdicts
        results["verdict"] = self._generate_verdict(metrics)

        return results

    def _calculate_raw_metrics(self, raw_games, total_games):
        total_panic_moves = 0
        games_with_time_pressure = 0

        for game in raw_games:
            clocks = game.get("clocks", [])
            if not clocks: continue

            user_color = game.get("user_color", "white")
            start_idx = 0 if user_color == "white" else 1
            user_clocks = clocks[start_idx::2]

            panic_moves_in_game = sum(1 for t in user_clocks if t < 15)
            total_panic_moves += panic_moves_in_game

            if panic_moves_in_game > 3:
                games_with_time_pressure += 1

        return {
            "panic_rate": (games_with_time_pressure / total_games) * 100,
            "avg_panic_moves": total_panic_moves / total_games
        }

    def _format_results(self, metrics):
        return {
            "panic_rate": {
                "raw": round(metrics["panic_rate"], 1),
                "peer": self.PEER_BENCHMARKS["panic_rate"],
                "peer_source": self.PEER_SOURCE,
                "visual": MetricVisualizer.get_bars(metrics["panic_rate"], self.PEER_BENCHMARKS["panic_rate"],
                                                    "accuracy", reverse=True)
            },
            "avg_panic_moves": {
                "raw": round(metrics["avg_panic_moves"], 1),
                "peer": self.PEER_BENCHMARKS["avg_panic_moves"],
                "peer_source": self.PEER_SOURCE,
                "visual": MetricVisualizer.get_bars(metrics["avg_panic_moves"], self.PEER_BENCHMARKS["avg_panic_moves"],
                                                    "accuracy", reverse=True)
            }
        }

    def _generate_verdict(self, metrics):
        """Builds 3 verdicts: weak spot, strong spot, advice."""
        messages = []
        rate = metrics["panic_rate"]
        avg = metrics["avg_panic_moves"]

        # 1. Weak spot
        if rate > 30:
            messages.append("You are entering severe time trouble too often, which limits your ability to calculate deeply.")
        elif avg > 3:
            messages.append(
                "You tend to make several panicked moves in a single game, indicating unstable time usage."
            )
        else:
            messages.append("Your time management is in good shape — no critical failures were detected.")

        if rate < 10:
            messages.append(
                "Your time control is excellent: you rarely find yourself in real time trouble."
            )
        else:
            messages.append("You play confidently with the clock, leaving enough margin for complex positions.")

        if rate > 20 or avg > 2:
            messages.append(
                "Try deciding faster in the opening to build a time buffer for later complications."
            )
        else:
            messages.append("Keep up the pace — your tempo allows comfortable completion of most games.")

        return messages