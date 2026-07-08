import contextlib
from unittest.mock import Mock

from django.test import SimpleTestCase

from analyzer.services.pipeline import ChessAnalysisPipeline


class ChessAnalysisPipelineTests(SimpleTestCase):
    def test_returns_no_games_error_without_starting_engine(self):
        api_client = Mock()
        api_client.get_games = Mock(return_value=[])
        engine_factory = Mock(side_effect=AssertionError("engine should not start"))

        pipeline = ChessAnalysisPipeline(
            api_client=api_client,
            engine_factory=engine_factory,
            stats_engine=Mock(),
            opening_engine=Mock(),
            skills_engine=Mock(),
            time_engine=Mock(),
            phase_engine=Mock(),
            piece_engine=Mock(),
        )

        result = pipeline.run_analysis(username="tester", platform="lichess", limit=10)

        self.assertEqual(result, {"error": "No games found"})
        engine_factory.assert_not_called()

    def test_returns_structured_error_when_stockfish_is_missing(self):
        api_client = Mock()
        api_client.get_games = Mock(return_value=[{"pgn": "1. e4"}])

        pipeline = ChessAnalysisPipeline(
            api_client=api_client,
            stats_engine=Mock(),
            opening_engine=Mock(),
            skills_engine=Mock(),
            time_engine=Mock(),
            phase_engine=Mock(),
            piece_engine=Mock(),
            stockfish_path="/definitely/missing/stockfish",
        )

        result = pipeline.run_analysis(username="tester", platform="lichess", limit=10)

        self.assertIn("Stockfish", result["error"])
        self.assertEqual(result["status"], "error")

    def test_returns_summary_and_snapshot_for_successful_analysis(self):
        api_client = Mock()
        api_client.get_games = Mock(return_value=[{"pgn": "1. e4", "user_color": "white", "user_result": "win"}])

        stats_engine = Mock()
        stats_engine.analyze_profile.return_value = {
            "overall": {"win_rate": 58.0, "total_games": 1},
            "modes": {"rapid": {"avg_peer_accuracy": 56.6, "avg_rating": 1063.0, "avg_peer_rating": 1054.0}},
        }

        opening_engine = Mock()
        opening_engine.analyze_openings.return_value = {"top_openings_white": []}

        skills_engine = Mock()
        skills_engine.analyze_skills_from_traces.return_value = {
            "overall": {
                "avg_accuracy": 42.6,
                "avg_resourcefulness": 55.6,
                "avg_conversion": 50.0,
                "peer_accuracy": {"value": 65.0, "source": "estimated"},
                "total_games_analyzed": 1,
            },
            "games": [],
        }

        time_engine = Mock()
        time_engine.analyze_time.return_value = {"panic_rate": {"raw": 0.0, "peer": 20.0}}

        phase_engine = Mock()
        phase_engine.analyze_from_traces.return_value = {
            "metrics": [{"name": "opening", "value": 0.9, "peer_average": 0.9}]
        }

        piece_engine = Mock()
        piece_engine.analyze_from_traces.return_value = {
            "metrics": [{"name": "P", "value": 45.0, "peer_average": 45.0}]
        }

        game_evaluator = Mock()
        game_evaluator.evaluate.return_value = None

        pipeline = ChessAnalysisPipeline(
            api_client=api_client,
            stats_engine=stats_engine,
            opening_engine=opening_engine,
            skills_engine=skills_engine,
            time_engine=time_engine,
            phase_engine=phase_engine,
            piece_engine=piece_engine,
            game_evaluator=game_evaluator,
            stockfish_path=__file__,
            engine_factory=lambda _path: contextlib.nullcontext(Mock()),
        )

        result = pipeline.run_analysis(username="tester", platform="lichess", limit=10)

        self.assertIn("summary", result)
        self.assertIn("snapshot", result)
        self.assertIn("highlights", result)
        self.assertIn("sections", result)
        self.assertEqual(result["snapshot"]["accuracy"], 42.6)
        self.assertEqual(result["snapshot"]["win_rate"], 58.0)

    def test_prefers_actual_peer_accuracy_over_estimated_baseline(self):
        api_client = Mock()
        api_client.get_games = Mock(return_value=[{"pgn": "1. e4", "user_color": "white", "user_result": "draw"}])

        stats_engine = Mock()
        stats_engine.analyze_profile.return_value = {
            "overall": {"win_rate": 60.0, "total_games": 1},
            "modes": {"rapid": {"avg_peer_accuracy": 55.0, "avg_rating": 1100.0, "avg_peer_rating": 1080.0}},
        }

        opening_engine = Mock()
        opening_engine.analyze_openings.return_value = {"top_openings_white": []}

        skills_engine = Mock()
        skills_engine.analyze_skills_from_traces.return_value = {
            "overall": {
                "avg_accuracy": 62.0,
                "avg_resourcefulness": 70.0,
                "avg_conversion": 50.0,
                "peer_accuracy": {"value": 57.5, "source": "actual"},
                "total_games_analyzed": 1,
            },
            "games": [],
        }

        time_engine = Mock()
        time_engine.analyze_time.return_value = {"panic_rate": {"raw": 5.0, "peer": 20.0}}

        phase_engine = Mock()
        phase_engine.analyze_from_traces.return_value = {}

        piece_engine = Mock()
        piece_engine.analyze_from_traces.return_value = {}

        game_evaluator = Mock()
        game_evaluator.evaluate.return_value = None

        pipeline = ChessAnalysisPipeline(
            api_client=api_client,
            stats_engine=stats_engine,
            opening_engine=opening_engine,
            skills_engine=skills_engine,
            time_engine=time_engine,
            phase_engine=phase_engine,
            piece_engine=piece_engine,
            game_evaluator=game_evaluator,
            stockfish_path=__file__,
            engine_factory=lambda _path: contextlib.nullcontext(Mock()),
        )

        result = pipeline.run_analysis(username="tester", platform="lichess", limit=10)

        self.assertEqual(result["summary"]["peer_accuracy_source"], "actual")
        self.assertIn("62.0%", result["summary"]["summary_text"])

    def test_parse_pgn_games_returns_structured_games(self):
        from analyzer.services.chess_api import ChessAPIClient

        pgn_text = (
            "[Event \"Test\"]\n"
            "[Site \"Local\"]\n"
            "[Date \"2026.06.29\"]\n"
            "[Round \"1\"]\n"
            "[White \"Alice\"]\n"
            "[Black \"Bob\"]\n"
            "[Result \"1-0\"]\n"
            "[WhiteElo \"1600\"]\n"
            "[BlackElo \"1500\"]\n"
            "\n"
            "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3\n"
        )

        client = ChessAPIClient()
        games = client.parse_pgn_games(pgn_text, username="Alice", platform="pgn")

        self.assertEqual(len(games), 1)
        game = games[0]
        self.assertEqual(game["platform"], "pgn")
        self.assertEqual(game["user_color"], "white")
        self.assertEqual(game["user_result"], "win")
        self.assertEqual(game["user_rating"], 1600)
        self.assertEqual(game["opponent_rating"], 1500)
        self.assertIsInstance(game["opening"], dict)
        self.assertIn("name", game["opening"])
