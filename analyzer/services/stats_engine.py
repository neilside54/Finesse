import io
import chess.pgn
import random
from typing import List, Dict, Any
from collections import Counter, defaultdict


class ChessStatsEngine:
    """
    Ядро анализатора: обрабатывает PGN данные, рассчитывает точность,
    активность фигур и формирует психологические инсайты (Skills).
    """

    PIECE_MAP = {
        chess.PAWN: "pawn",
        chess.KNIGHT: "knight",
        chess.BISHOP: "bishop",
        chess.ROOK: "rook",
        chess.QUEEN: "queen",
        chess.KING: "king"
    }

    def analyze_profile(self, games: List[Dict[str, Any]], username: str) -> Dict[str, Any]:
        """
        Главный метод: агрегирует данные по всем играм пользователя.
        """
        total_games_received = len(games)

        report = {
            "overall": {
                "total_games": total_games_received,
                "platforms": dict(Counter(g["platform"] for g in games)),
                # Если игр мало, предупреждаем пользователя
                "warning": "Low game count. Play more games for better accuracy." if total_games_received < 50 else None
            },
            "by_mode": defaultdict(lambda: {
                "games_count": 0,
                "total_moves": 0,
                "user_accuracies": [],
                "peer_accuracies": [],
                "piece_usage": Counter(),
                "avg_rating": 0,
                "peer_avg_rating": 0
            })
        }

        for game_data in games:
            mode = game_data.get("time_class", "other")
            stats = report["by_mode"][mode]

            if not game_data.get("pgn"):
                continue

            pgn_io = io.StringIO(game_data["pgn"])
            game = chess.pgn.read_game(pgn_io)

            if not game:
                continue

            # Определяем цвет игрока на основе заголовков PGN
            white_header = game.headers.get("White", "").lower()
            is_white = white_header == username.lower()

            # 1. Считаем ходы и активность фигур
            move_count, piece_counts = self._analyze_moves(game, is_white)

            # 2. Расчет Accuracy (Mock-логика)
            # В будущем здесь будет: self._calculate_stockfish_accuracy(game)
            user_acc, peer_acc = self._calculate_mock_accuracy(
                game_data["user_result"],
                game_data["user_rating"],
                game_data["opponent_rating"]
            )

            # Обновляем статистику режима
            stats["games_count"] += 1
            stats["total_moves"] += move_count
            stats["user_accuracies"].append(user_acc)
            stats["peer_accuracies"].append(peer_acc)
            stats["piece_usage"].update(piece_counts)

            if game_data["user_rating"]:
                stats["avg_rating"] += game_data["user_rating"]
            if game_data["opponent_rating"]:
                stats["peer_avg_rating"] += game_data["opponent_rating"]

        return self._finalize_report(report)

    def _analyze_moves(self, game: chess.pgn.Game, is_white: bool) -> (int, Counter):
        """Проходит по дереву ходов и собирает статистику использования фигур."""
        move_count = 0
        piece_counts = Counter()
        board = game.board()

        for move in game.mainline_moves():
            if board.turn == is_white:
                piece_to_move = board.piece_at(move.from_square)
                if piece_to_move:
                    piece_type = piece_to_move.piece_type
                    piece_counts[self.PIECE_MAP[piece_type]] += 1
                    move_count += 1
            board.push(move)

        return move_count, piece_counts

    def _calculate_mock_accuracy(self, result: str, user_rating: int, opp_rating: int) -> (float, float):
        """Эмуляция расчета точности."""
        base_map = {"win": 74.0, "draw": 68.0, "loss": 56.0}
        base_acc = base_map.get(result, 65.0)

        rating_bonus = (user_rating or 1200) / 2000.0
        user_acc = base_acc + random.uniform(-6, 6) + rating_bonus

        peer_rating_bonus = (opp_rating or 1200) / 2000.0
        peer_acc = base_acc + random.uniform(-6, 6) + peer_rating_bonus

        # Калибруем под реальные шахматные рамки
        user_acc = max(min(user_acc, 99.5), 20.0)
        peer_acc = max(min(peer_acc, 99.5), 20.0)

        return round(user_acc, 2), round(peer_acc, 2)

    def _generate_skills_feedback(self, user_acc: float, peer_acc: float, mode: str) -> Dict[str, str]:
        """Генерация фидбека в стиле Lichess Coach Companion."""
        diff = user_acc - peer_acc
        if diff > 2.0:
            return {
                "title": "High Accuracy",
                "desc": f"Your accuracy in {mode} is better than your peers. You make remarkably precise moves based on tactical alignment."
            }
        elif diff < -2.0:
            return {
                "title": "Needs Improvement",
                "desc": f"Your peers are currently playing slightly tighter chess in {mode}. Watch out for minor tactical inaccuracies in complex positions."
            }
        else:
            return {
                "title": "Solid Performance",
                "desc": f"You are head-to-head with your peers in {mode}. Your tactical foundation matches players of your exact caliber."
            }

    def _finalize_report(self, report: Dict) -> Dict:
        """Усреднение данных и генерация финального JSON-структурированного отчета."""
        final_by_mode = {}

        for mode, data in report["by_mode"].items():
            count = data["games_count"]
            if count == 0:
                continue

            avg_user_acc = round(sum(data["user_accuracies"]) / count, 1)
            avg_peer_acc = round(sum(data["peer_accuracies"]) / count, 1)

            final_by_mode[mode] = {
                "games_count": count,
                "total_moves": data["total_moves"],
                "avg_user_accuracy": avg_user_acc,
                "avg_peer_accuracy": avg_peer_acc,
                "avg_rating": int(data["avg_rating"] / count) if data["avg_rating"] else None,
                "avg_peer_rating": int(data["peer_avg_rating"] / count) if data["peer_avg_rating"] else None,
                "skills": self._generate_skills_feedback(avg_user_acc, avg_peer_acc, mode),
                "piece_activity_percentage": {
                    p: round((c / data["total_moves"]) * 100, 1)
                    for p, c in data["piece_usage"].items()
                }
            }

        return {
            "summary": report["overall"],
            "modes": final_by_mode
        }