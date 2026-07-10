from collections import defaultdict
from analyzer.utils.visualizer import MetricVisualizer


class ChessOpeningEngine:
    PEER_BENCHMARK = 45.0

    def analyze_openings(self, formatted_games, username):
        stats = {
            "white": defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "total": 0, "eco": "???"}),
            "black": defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "total": 0, "eco": "???"})
        }
        family_stats = {
            "white": defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "total": 0}),
            "black": defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "total": 0})
        }

        # 1. Сбор данных
        for game in formatted_games:
            opening_data = game.get("opening", {})
            if not opening_data: continue

            full_name = opening_data.get("name", "Unknown Opening")
            eco_code = opening_data.get("eco", "???")
            user_color = game.get("user_color", "white")
            result = game.get("user_result", "draw")

            base_family = full_name.split(":")[0].split(",")[0].strip()

            current_stats = stats[user_color][full_name]
            current_stats["total"] += 1
            current_stats["eco"] = eco_code

            current_family = family_stats[user_color][base_family]
            current_family["total"] += 1

            if result == "win":
                current_stats["wins"] += 1
                current_family["wins"] += 1
            elif result == "loss":
                current_stats["losses"] += 1
                current_family["losses"] += 1
            else:
                current_stats["draws"] += 1
                current_family["draws"] += 1

        # 2. Обработка
        top_white = self._format_and_sort(stats["white"])
        top_black = self._format_and_sort(stats["black"])
        bad_openings = self._find_bad_openings(family_stats)

        weak_openings = {
            "white": [entry for entry in bad_openings if entry["color"] == "white"][:3],
            "black": [entry for entry in bad_openings if entry["color"] == "black"][:3],
        }

        strong_openings = {
            "white": top_white[:3],
            "black": top_black[:3],
        }

        opening_trends = self._build_opening_trends(family_stats)

        # 3. Генерация вердикта (всего 3 пункта)
        verdict = self._generate_verdict(top_white, top_black, bad_openings)

        return {
            "top_openings_white": top_white[:5],
            "top_openings_black": top_black[:5],
            "weak_openings": weak_openings,
            "strong_openings": strong_openings,
            "opening_trends": opening_trends,
            "verdict": verdict,
        }

    def _generate_verdict(self, top_white, top_black, weak_openings):
        """Formulates a compact opening diagnosis and advice."""
        messages = []

        if weak_openings:
            worst = weak_openings[0]
            messages.append(
                f"Your biggest opening weakness is the {worst['opening_family']} system as {worst['color']} — it has a {worst['win_rate']}% win rate over {worst['total_games']} games."
            )
        else:
            messages.append("No major opening weaknesses were detected in the available game sample.")

        best_all = sorted(top_white + top_black, key=lambda x: (x['win_rate'], x['total_games']), reverse=True)
        if best_all:
            best = best_all[0]
            messages.append(
                f"Your strongest opening line is '{best['opening']}' with a {best['win_rate']}% win rate."
            )
        else:
            messages.append("There is not enough opening data to identify a stable best line.")

        if weak_openings:
            messages.append(
                "Focus your study on one or two main opening families and avoid spreading your preparation too thin."
            )
        else:
            messages.append(
                "Keep reinforcing your main opening systems and avoid adding too many new lines until your current repertoire is stable."
            )

        return messages

    def _find_bad_openings(self, family_stats):
        bad_openings = []
        for color in ["white", "black"]:
            for family_name, data in family_stats[color].items():
                if family_name == "Unknown Opening":
                    continue
                total = data["total"]
                win_rate = round((data["wins"] / total) * 100, 1) if total > 0 else 0.0

                if (total >= 3 and win_rate < 40.0) or (total == 2 and win_rate == 0.0):
                    bad_openings.append({
                        "opening_family": family_name,
                        "color": color,
                        "total_games": total,
                        "win_rate": win_rate,
                        "visual": MetricVisualizer.get_bars(win_rate, self.PEER_BENCHMARK, "accuracy"),
                        "severity": "CRITICAL" if win_rate == 0.0 else "WARNING",
                        "trend": "declining",
                    })
        return sorted(bad_openings, key=lambda x: (x["severity"] != "CRITICAL", x["win_rate"]))

    def _build_opening_trends(self, family_stats):
        trends = []
        for color in ["white", "black"]:
            families = []
            for family_name, data in family_stats[color].items():
                if family_name == "Unknown Opening":
                    continue
                total = data["total"]
                win_rate = round((data["wins"] / total) * 100, 1) if total > 0 else 0.0
                families.append({
                    "opening_family": family_name,
                    "color": color,
                    "total_games": total,
                    "win_rate": win_rate,
                })
            families.sort(key=lambda x: (-x["total_games"], -x["win_rate"]))
            for entry in families[:3]:
                entry["trend_label"] = (
                    "Popular and performing" if entry["win_rate"] >= 50.0 else "Popular but inconsistent"
                )
                entry["direction"] = "positive" if entry["win_rate"] >= 50.0 else "neutral"
                trends.append(entry)
        return trends

    def _format_and_sort(self, color_stats):
        formatted = []
        for name, data in color_stats.items():
            total = data["total"]
            win_rate = round((data["wins"] / total) * 100, 1) if total > 0 else 0.0
            formatted.append({
                "opening": name,
                "eco": data["eco"],
                "total_games": total,
                "win_rate": win_rate,
                "visual": MetricVisualizer.get_bars(win_rate, self.PEER_BENCHMARK, "accuracy")
            })
        return sorted(formatted, key=lambda x: x["total_games"], reverse=True)