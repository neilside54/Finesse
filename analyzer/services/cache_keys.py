"""
Cache key helpers for analysis reports.

Both the Celery pipeline (full Stockfish-backed report) and the synchronous
fallback view (lightweight stats-only report) cache their results, but they
produce different response shapes — so they use distinct key prefixes to
avoid one overwriting/serving the other's format.
"""

from __future__ import annotations

import hashlib
from typing import Optional


def _subject_key(username: Optional[str], pgn_text: Optional[str]) -> str:
    """
    Identifies *what* is being analyzed: a platform username, or an uploaded
    PGN blob (hashed, since PGN text can be long/arbitrary and isn't safe to
    use directly as part of a cache key).
    """
    if username:
        return f"user:{username.strip().lower()}"
    if pgn_text:
        digest = hashlib.sha256(pgn_text.encode("utf-8")).hexdigest()[:16]
        return f"pgn:{digest}"
    return "unknown"


def full_report_cache_key(
    platform: str, username: Optional[str], limit: int, pgn_text: Optional[str] = None
) -> str:
    """Key for the full pipeline report (Stockfish-backed, run via Celery)."""
    return f"report:full:v1:{platform}:{_subject_key(username, pgn_text)}:{limit}"


def sync_report_cache_key(
    platform: str, username: Optional[str], limit: int, pgn_text: Optional[str] = None
) -> str:
    """Key for the lightweight synchronous fallback report (stats only, no Stockfish)."""
    return f"report:sync:v1:{platform}:{_subject_key(username, pgn_text)}:{limit}"