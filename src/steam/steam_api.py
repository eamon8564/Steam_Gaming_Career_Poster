"""Public Steam Web API access. Keys never appear in error messages."""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.core.models import Game, GameLibrary
from src.common.utils import PROJECT_DIR


class SteamError(Exception):
    """A Steam problem that can be shown directly to the user."""


def read_api_key():
    """Prefer the environment, then an ignored local text file."""
    key = os.environ.get("STEAM_WEB_API_KEY", "").strip()
    if not key:
        try:
            key = (PROJECT_DIR / "steam_api_key.txt").read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
        except OSError:
            raise SteamError("Cannot read the local API key file.") from None
    if not key:
        raise SteamError("Set STEAM_WEB_API_KEY or put your Web API key in "
                         "steam_api_key.txt in the application folder. Demo Mode needs no key.")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", key):
        raise SteamError("The Web API key should contain 32 hexadecimal characters.")
    return key


def validate_steam_id(steam_id):
    """Accept only the 17-digit individual-account SteamID64 form."""
    if not isinstance(steam_id, str) or not re.fullmatch(r"7656119[0-9]{10}", steam_id):
        raise SteamError("Enter a 17-digit SteamID64 beginning with 7656119.")
    return steam_id


class SteamClient:
    """Load visible owned games over HTTPS using a local Web API key."""

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else read_api_key()

    def _get(self, endpoint, parameters):
        parameters = dict(parameters, key=self.api_key, format="json")
        url = "https://api.steampowered.com/" + endpoint + "?" + urlencode(parameters)
        try:
            request = Request(url, headers={"User-Agent": "SteamGamingJourney/1.0"})
            with urlopen(request, timeout=15) as response:
                raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise SteamError("Steam returned too much data. Try again later.")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except HTTPError as error:
            if error.code in (401, 403):
                raise SteamError("Steam rejected the API key. Check your local key.") from None
            raise SteamError("Steam is temporarily unavailable or rate-limited. Try later.") from None
        except (URLError, OSError):
            raise SteamError("Steam could not be reached or timed out. Check your connection.") from None
        except (ValueError, UnicodeError):
            raise SteamError("Steam returned invalid data. Please try again later.") from None

    def load_library(self, steam_id):
        """Return the same GameLibrary used by Demo Mode."""
        steam_id = validate_steam_id(steam_id)
        data = self._get("IPlayerService/GetOwnedGames/v0001/", {
            "steamid": steam_id, "include_appinfo": 1,
            "include_played_free_games": 1,
        })
        response = data.get("response")
        if not isinstance(response, dict):
            raise SteamError("Steam returned an invalid library response.")
        if not response or ("games" not in response and response.get("game_count") != 0):
            raise SteamError("Steam did not return your library. Game Details may be private; "
                             "make them visible or use Demo Mode.")
        rows = response.get("games", [])
        try:
            if not isinstance(rows, list):
                raise ValueError()
            games = []
            for row in rows:
                games.append(Game(row["appid"], row.get("name", f"Game {row['appid']}"),
                                  row["playtime_forever"],
                                  last_played=row.get("rtime_last_played", row.get("last_playtime")),
                                  playtime_2weeks=row.get("playtime_2weeks")))
            library = GameLibrary(steam_id, games)
        except (ValueError, TypeError, KeyError):
            raise SteamError("Steam returned malformed game data. Try again later.") from None
        # A missing display name should never discard an otherwise valid library.
        try:
            profile = self._get("ISteamUser/GetPlayerSummaries/v0002/", {"steamids": steam_id})
            players = profile.get("response", {}).get("players", [])
            if players and isinstance(players[0].get("personaname"), str):
                library.owner_name = players[0]["personaname"] or steam_id
        except (SteamError, AttributeError, TypeError, KeyError):
            pass
        return library
