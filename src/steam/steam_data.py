"""Select all games or the known recently active subset, without inventing history."""

from datetime import datetime, timezone, timedelta
from src.core.models import GameLibrary


def select_library(library, mode='all', now=None):
    """Return a library, scope note, and missing-date count.

    recent_year means LAST PLAYED within 365 days, weighted by LIFETIME minutes.
    Missing dates for games with positive playtime are unknown, not 'old'.
    """
    if mode == 'all':
        return library, 'ALL GAMES / LIFETIME PLAYTIME', 0
    if mode != 'recent_year':
        raise ValueError('Unknown poster mode.')
    now = now or datetime.now(timezone.utc)
    cutoff = int((now - timedelta(days=365)).timestamp())
    current = int(now.timestamp())
    games, missing = [], 0
    for game in library.games:
        if not game.has_been_played():
            continue
        last = game.last_played
        if last is None or last <= 0 or last > current:
            missing += 1
        elif last >= cutoff:
            games.append(game)
    if missing and missing == len(library.played_games()):
        raise ValueError('Steam supplied no usable last-played dates. Recent-year filtering is unavailable; use All games.')
    note = 'PLAYED IN LAST 365 DAYS / LIFETIME HOURS, NOT ANNUAL HOURS'
    if missing:
        note += f' / {missing} UNKNOWN DATES EXCLUDED'
    return GameLibrary(library.owner_name, games), note, missing
