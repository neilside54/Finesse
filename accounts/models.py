import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model for Finesse.

    Extends Django's AbstractUser with fields specific to a chess analytics
    platform.  Using a custom User model from day one avoids the painful
    migration that would be required if we switched later.
    """

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.username


class LinkedChessAccount(models.Model):
    """A chess platform account linked to a Finesse user.

    Users can link multiple accounts (e.g. both a Chess.com and a Lichess
    account) and mark one as primary for quick analysis.
    """

    PLATFORM_CHOICES = [
        ("chess.com", "Chess.com"),
        ("lichess", "Lichess"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="linked_chess_accounts",
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_username = models.CharField(
        max_length=150,
        help_text="Username on the chess platform.",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="If true, this is the default account used for quick analysis.",
    )
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Cached rating from the last sync.",
    )
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "-linked_at"]
        unique_together = ["user", "platform", "platform_username"]
        indexes = [
            models.Index(fields=["user", "platform"]),
        ]

    def __str__(self) -> str:
        return f"{self.platform}:{self.platform_username} ({self.user})"
