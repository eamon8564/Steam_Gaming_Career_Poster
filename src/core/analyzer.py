"""Reproducible statistics and transparent rules; no GUI or network code."""


class JourneyAnalyzer:
    """Analyse a GameLibrary using simple course-level Python."""

    def __init__(self, library):
        self.library = library

    def top_game(self):
        """Return the favourite game, or None when nothing was played."""
        games = self.library.top_games(1)
        return games[0] if games else None

    def top_n_share(self, n=3):
        """Return a fraction in [0, 1], safely handling zero playtime."""
        total = self.library.total_playtime_minutes()
        if total == 0:
            return 0.0
        minutes = sum(game.playtime_minutes for game in self.library.top_games(n))
        return minutes / total

    def count_over_hours(self, hours):
        """Count games at or above the supplied threshold (inclusive)."""
        return sum(game.playtime_minutes >= hours * 60 for game in self.library.games)

    def count_unplayed(self):
        """Count owned games with exactly zero recorded minutes."""
        return self.library.total_games() - len(self.library.played_games())

    def player_style_label(self):
        """Apply documented rules in priority order."""
        if not self.library.played_games():
            return "Journey Ahead"
        if self.top_n_share(3) >= 0.60:
            return "Focused Player"
        if len(self.library.played_games()) >= 20:
            return "Variety Player"
        return "Balanced Player"

    def summary_dict(self):
        """Return display-ready facts without changing the source data."""
        favourite = self.top_game()
        return {
            "owner_name": self.library.owner_name,
            "total_games": self.library.total_games(),
            "total_hours": self.library.total_playtime_minutes() / 60,
            "played_games": len(self.library.played_games()),
            "most_played": favourite.name if favourite else "No games played yet",
            "top_three_share": self.top_n_share(3),
            "games_50_hours": self.count_over_hours(50),
            "games_100_hours": self.count_over_hours(100),
            "unplayed_games": self.count_unplayed(),
            "player_style": self.player_style_label(),
            "deep_dive": self.count_over_hours(100) >= 5,
        }
