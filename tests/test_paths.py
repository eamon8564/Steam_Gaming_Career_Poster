"""Protect the public key location and resources after source reorganisation."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common.paths import PROJECT_DIR
from src.common.utils import ART_DIR, DEMO_PATH, load_demo
from src.steam.steam_api import read_api_key


class ProjectPathTests(unittest.TestCase):
    def test_resources_are_beside_the_public_entry_point(self):
        self.assertEqual(PROJECT_DIR, Path(__file__).resolve().parents[1])
        self.assertTrue((PROJECT_DIR / 'main.py').is_file())
        self.assertEqual(DEMO_PATH, PROJECT_DIR / 'data' / 'demo_library.json')
        self.assertEqual(ART_DIR, PROJECT_DIR / 'cache')
        self.assertEqual(load_demo().total_games(), 15)

    def test_local_key_is_read_from_application_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'steam_api_key.txt').write_text('a' * 32, encoding='utf-8')
            inner = root / 'src' / 'steam'
            inner.mkdir(parents=True)
            (inner / 'steam_api_key.txt').write_text('not-the-root-key', encoding='utf-8')
            with patch.dict(os.environ, {}, clear=True), patch('src.steam.steam_api.PROJECT_DIR', root):
                self.assertEqual(read_api_key(), 'a' * 32)

    def test_environment_key_takes_priority_without_reading_a_file(self):
        with patch.dict(os.environ, {'STEAM_WEB_API_KEY': 'b' * 32}, clear=True):
            with patch('pathlib.Path.read_text', side_effect=AssertionError('No file is needed')):
                self.assertEqual(read_api_key(), 'b' * 32)


if __name__ == '__main__':
    unittest.main()
