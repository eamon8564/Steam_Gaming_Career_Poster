"""Optional desktop OpenID flow, isolated from the GUI and API loader."""

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
import webbrowser

from src.steam.steam_api import SteamError, validate_steam_id

OPENID_URL = "https://steamcommunity.com/openid/login"
OPENID_NS = "http://specs.openid.net/auth/2.0"


def verify_response(fields, return_to):
    """Bind the assertion to this request, then verify its signature at Steam."""
    if fields.get("openid.mode") == "cancel":
        raise SteamError("Steam sign-in was cancelled. You can use Demo Mode.")
    required_signed = {"op_endpoint", "claimed_id", "identity", "return_to",
                       "response_nonce", "assoc_handle"}
    signed = set(fields.get("openid.signed", "").split(","))
    identity = fields.get("openid.claimed_id", "")
    match = re.fullmatch(r"https?://steamcommunity\.com/openid/id/(7656119[0-9]{10})", identity)
    if (fields.get("openid.ns") != OPENID_NS
            or fields.get("openid.mode") != "id_res"
            or fields.get("openid.op_endpoint") != OPENID_URL
            or fields.get("openid.return_to") != return_to
            or fields.get("openid.identity") != identity
            or not required_signed.issubset(signed)
            or not fields.get("openid.sig") or not match):
        raise SteamError("Steam sign-in could not be verified. Please try again.")
    try:
        issued = datetime.strptime(fields["openid.response_nonce"][:20],
                                   "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if abs((datetime.now(timezone.utc) - issued).total_seconds()) > 300:
            raise ValueError()
    except (KeyError, ValueError):
        raise SteamError("Steam sign-in expired. Please sign in again.") from None
    verification = {key: value for key, value in fields.items() if key.startswith("openid.")}
    verification["openid.mode"] = "check_authentication"
    try:
        request = Request(OPENID_URL, data=urlencode(verification).encode("utf-8"))
        with urlopen(request, timeout=15) as response:
            lines = response.read(16384).decode("utf-8").splitlines()
        if "is_valid:true" not in lines:
            raise SteamError("Steam rejected the sign-in response. Please try again.")
    except (OSError, UnicodeError):
        raise SteamError("Could not verify sign-in with Steam. Check your connection.") from None
    return validate_steam_id(match.group(1))


def sign_in(cancel, timeout=180):
    """Open Steam, accept one verified callback on loopback, and close the server."""
    state = secrets.token_urlsafe(32)
    result = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        """Handle only this login attempt; never log query strings."""

        def log_message(self, format, *args):
            pass

        def setup(self):
            self.request.settimeout(2)
            super().setup()

        def do_GET(self):
            parts = urlsplit(self.path)
            query = parse_qs(parts.query, keep_blank_values=True)
            if (parts.path != "/callback" or query.get("state") != [state]
                    or any(len(values) != 1 for values in query.values())):
                self.send_error(400, "Invalid callback")
                return
            fields = {key: values[0] for key, values in query.items()}
            try:
                result["steam_id"] = verify_response(fields, return_to)
                message = "Steam sign-in verified. You can return to Steam Gaming Journey."
            except SteamError as error:
                result["error"] = error
                message = "Sign-in was not completed. Return to the app to try again."
            content = message.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            try:
                self.wfile.write(content)
            except OSError:
                pass

    try:
        server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
    except OSError:
        raise SteamError("Cannot start local sign-in. Try loading by SteamID instead.") from None
    with server:
        server.timeout = 0.5
        origin = f"http://127.0.0.1:{server.server_port}"
        return_to = origin + "/callback?" + urlencode({"state": state})
        query = {
            "openid.ns": OPENID_NS, "openid.mode": "checkid_setup",
            "openid.return_to": return_to, "openid.realm": origin + "/",
            "openid.identity": OPENID_NS + "/identifier_select",
            "openid.claimed_id": OPENID_NS + "/identifier_select",
        }
        try:
            opened = webbrowser.open(OPENID_URL + "?" + urlencode(query))
        except webbrowser.Error:
            opened = False
        if not opened:
            raise SteamError("The browser could not open. Try loading by SteamID instead.")
        deadline = time.monotonic() + timeout
        while not result and not cancel.is_set() and time.monotonic() < deadline:
            server.handle_request()
    if cancel.is_set():
        raise SteamError("Steam sign-in cancelled.")
    if "error" in result:
        raise result["error"]
    if "steam_id" not in result:
        raise SteamError("Steam sign-in timed out. Please try again or use Demo Mode.")
    return result["steam_id"]
