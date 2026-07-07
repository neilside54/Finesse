from django.conf import settings
from django.db import models


class SavedAnalysis(models.Model):
    """
    A completed analysis report saved to a user's library.
    Guests can run analyses freely; logging in lets them persist results
    here and revisit them later from a personal history page.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_analyses",
    )
    task_id = models.CharField(max_length=255, db_index=True)
    platform = models.CharField(max_length=20, default="unknown")
    subject = models.CharField(
        max_length=150,
        help_text="Username analysed or 'PGN Upload'.",
    )
    total_games = models.PositiveIntegerField(default=0)
    # Store the full report JSON so the results page can load it
    # without re-running the pipeline.
    report = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.subject} ({self.platform}) — {self.total_games} games"


class RatingAccuracySample(models.Model):
    """
    A single real, measured accuracy data point for one game: the opponent's
    rating and the accuracy they actually played with, as computed by
    ChessSkillsEngine/GameEvaluator from a Stockfish-evaluated game.

    These accumulate over time as real users get their games analyzed.
    Once there's enough volume, the per-rating-bucket average computed from
    this table can replace (or validate) the hand-picked RATING_ACCURACY_CURVE
    estimate currently used as a fallback in stats_engine.py — turning
    "peer accuracy" from an educated guess into an actual community
    benchmark, without requiring any change to the public API response
    shape (it stays the source feeding the same field).
    """

    TIME_CLASS_CHOICES = [
        ("bullet", "Bullet"),
        ("blitz", "Blitz"),
        ("rapid", "Rapid"),
        ("classical", "Classical"),
        ("daily", "Daily"),
        ("correspondence", "Correspondence"),
        ("unknown", "Unknown"),
    ]

    PLATFORM_CHOICES = [
        ("chess.com", "Chess.com"),
        ("lichess", "Lichess"),
        ("pgn", "Uploaded PGN"),
    ]

    rating = models.PositiveIntegerField(
        help_text="Opponent's rating in the game this sample was measured from."
    )
    accuracy = models.FloatField(
        help_text="Opponent's measured accuracy (0-100) for that game, from GameEvaluator."
    )
    time_class = models.CharField(
        max_length=20, choices=TIME_CLASS_CHOICES, default="unknown", db_index=True
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            # Supports the main read pattern: "average accuracy for players
            # around rating X in time_class Y" — see RatingAccuracySample
            # .objects.benchmark_for(...) below.
            models.Index(fields=["time_class", "rating"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.platform}/{self.time_class} rating={self.rating} acc={self.accuracy}"

    @classmethod
    def benchmark_for(
        cls, time_class: str, rating: int, rating_window: int = 100
    ) -> float | None:
        """
        Average measured accuracy for samples within +/- rating_window of the
        given rating, in the given time_class. Returns None if there isn't
        enough data yet (caller should fall back to the estimated curve).
        """
        queryset = cls.objects.filter(
            time_class=time_class,
            rating__gte=rating - rating_window,
            rating__lte=rating + rating_window,
        )
        aggregate = queryset.aggregate(avg_accuracy=models.Avg("accuracy"), sample_count=models.Count("id"))
        if not aggregate["sample_count"]:
            return None
        return round(aggregate["avg_accuracy"], 1)