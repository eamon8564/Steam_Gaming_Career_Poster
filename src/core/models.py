"""Small data classes shared by the demo and Steam loaders."""


class Game:
    """A Steam game; playtime is always stored in minutes."""

    def __init__(self, app_id, name, playtime_minutes, image_url=None, last_played=None, playtime_2weeks=None):
        if type(app_id) is not int or app_id <= 0:
            raise ValueError("Game IDs must be positive integers.")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Each game needs a name.")
        if type(playtime_minutes) is not int or playtime_minutes < 0:
            raise ValueError("Playtime must be a non-negative number of minutes.")
        self.app_id = app_id
        self.name = name.strip()
        self.playtime_minutes = playtime_minutes
        self.image_url = image_url
        # Optional API fields: absence must not be silently changed to a zero.
        self.last_played = last_played if type(last_played) is int and last_played >= 0 else None
        self.playtime_2weeks = playtime_2weeks if type(playtime_2weeks) is int and playtime_2weeks >= 0 else None

    @property
    def playtime_hours(self):
        """Convert minutes to hours without rounding the source data."""
        return self.playtime_minutes / 60

    def has_been_played(self):
        """Whether this game has recorded playtime."""
        return self.playtime_minutes > 0


class GameLibrary:
    """One player's collection of Game objects."""

    def __init__(self, owner_name, games):
        if not isinstance(owner_name, str) or not owner_name.strip():
            raise ValueError("A library needs a player name.")
        self.owner_name = owner_name.strip()
        self.games = list(games)
        seen = set()
        for game in self.games:
            if not isinstance(game, Game) or game.app_id in seen:
                raise ValueError("The library contains an invalid or duplicate game.")
            seen.add(game.app_id)

    def total_games(self):
        """Count all owned games, including unplayed games."""
        return len(self.games)

    def total_playtime_minutes(self):
        """Sum the original minutes."""
        return sum(game.playtime_minutes for game in self.games)

    def played_games(self):
        """Return games with positive recorded playtime."""
        return [game for game in self.games if game.has_been_played()]

    def top_games(self, limit=12):
        """Rank played games by minutes; app ID breaks ties consistently."""
        ranked = sorted(self.played_games(),
                        key=lambda game: (-game.playtime_minutes, game.app_id))
        return ranked[:max(0, limit)]
