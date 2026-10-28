"""Exercise a real loopback callback with simulated Steam signature verification.

No external network, browser window, credentials or actual Steam login is used.
"""

from datetime import datetime, timezone
import io
from pathlib import Path
import socket
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.steam.steam_auth import OPENID_NS, OPENID_URL, sign_in
from src.steam.steam_api import SteamError


class CallbackTests(unittest.TestCase):
    def test_callback_state_verification_and_server_cleanup(self):
        callback_threads = []
        errors = []
        ports = []

        def fake_browser(login_url):
            self.assertTrue(login_url.startswith(OPENID_URL + '?'))
            query = parse_qs(urlsplit(login_url).query)
            return_to = query['openid.return_to'][0]
            ports.append(urlsplit(return_to).port)

            def send_callback():
                try:
                    wrong = return_to.split('?')[0] + '?state=incorrect'
                    try:
                        urlopen(wrong, timeout=3)
                        raise AssertionError('Wrong state was accepted')
                    except HTTPError as error:
                        self.assertEqual(error.code, 400)
                    identity = 'https://steamcommunity.com/openid/id/76561198000000000'
                    fields = {
                        'openid.ns': OPENID_NS, 'openid.mode': 'id_res',
                        'openid.op_endpoint': OPENID_URL, 'openid.identity': identity,
                        'openid.claimed_id': identity, 'openid.return_to': return_to,
                        'openid.response_nonce': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + 'test',
                        'openid.assoc_handle': 'test', 'openid.sig': 'test',
                        'openid.signed': 'op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle',
                    }
                    with urlopen(return_to + '&' + urlencode(fields), timeout=3) as response:
                        self.assertIn(b'verified', response.read())
                except Exception as error:
                    errors.append(error)

            thread = threading.Thread(target=send_callback, daemon=True)
            callback_threads.append(thread)
            thread.start()
            return True

        with patch('src.steam.steam_auth.webbrowser.open', side_effect=fake_browser):
            with patch('src.steam.steam_auth.urlopen', return_value=io.BytesIO(b'is_valid:true\n')):
                self.assertEqual(sign_in(threading.Event(), timeout=5), '76561198000000000')
        for thread in callback_threads:
            thread.join(timeout=4)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        with socket.socket() as connection:
            connection.settimeout(1)
            self.assertNotEqual(connection.connect_ex(('127.0.0.1', ports[0])), 0)

    @patch('src.steam.steam_auth.webbrowser.open', return_value=True)
    def test_timeout(self, browser):
        with self.assertRaisesRegex(SteamError, 'timed out'):
            sign_in(threading.Event(), timeout=0.01)

    @patch('src.steam.steam_auth.webbrowser.open', return_value=True)
    def test_cancel(self, browser):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaisesRegex(SteamError, 'cancelled'):
            sign_in(cancel)

    @patch('src.steam.steam_auth.webbrowser.open', return_value=False)
    def test_browser_failure(self, browser):
        with self.assertRaisesRegex(SteamError, 'browser could not open'):
            sign_in(threading.Event())


if __name__ == '__main__':
    unittest.main(verbosity=2)
