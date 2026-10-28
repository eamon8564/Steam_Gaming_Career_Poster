"""File loading and safe, optional Steam artwork downloads."""

import json
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.core.models import Game, GameLibrary

from src.common.paths import PROJECT_DIR
DEMO_PATH = PROJECT_DIR / "data" / "demo_library.json"
ART_DIR = PROJECT_DIR / "cache"


def load_demo(path=DEMO_PATH):
    """Read and validate a local JSON library; never access the network."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("games"), list):
            raise ValueError("Expected a player and a list of games.")
        games = []
        for row in data["games"]:
            if not isinstance(row, dict):
                raise ValueError("Each game must be a JSON object.")
            last = row.get("last_played")
            if "demo_days_ago" in row:
                last = int(time.time()) - int(row["demo_days_ago"]) * 86400
            games.append(Game(row["app_id"], row["name"], row["playtime_minutes"],
                              last_played=last, playtime_2weeks=row.get("playtime_2weeks")))
        return GameLibrary(data["owner_name"], games)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError("Cannot read demo data. Restore data/demo_library.json "
                         "and check game names, IDs and playtime.") from error


def download_covers(games, cancel=None):
    """Prefer 600x900 library artwork; fall back to store headers or placeholders."""
    try:
        ART_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    for game in games:
        if cancel is not None and cancel.is_set():
            return
        for filename, suffix in (("library_600x900.jpg", "_portrait.jpg"), ("header.jpg", ".jpg")):
            if cancel is not None and cancel.is_set():
                return
            target = ART_DIR / f"{game.app_id}{suffix}"
            if target.exists():
                continue
            url = ("https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/"
                   f"{game.app_id}/{filename}")
            try:
                request = Request(url, headers={"User-Agent": "SteamGamingJourney/1.0"})
                with urlopen(request, timeout=4) as response:
                    data = response.read(2_000_001)
                if len(data) <= 2_000_000 and data.startswith(b"\xff\xd8"):
                    target.write_bytes(data)
                    continue
            except (OSError, URLError):
                continue
