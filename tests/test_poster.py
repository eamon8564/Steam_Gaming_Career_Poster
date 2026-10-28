"""Run with the selected environment: python -m unittest discover -s career_poster/tests."""

from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core.config import PosterConfig
from src.core.models import Game, GameLibrary
from src.steam.steam_data import select_library
from src.poster.treemap_layout import group_games, squarify
from src.poster.image_renderer import PosterRenderer, Image
from src.steam.steam_api import SteamClient, SteamError
from src.common.utils import load_demo, download_covers


class GeometryTests(unittest.TestCase):
    def check_geometry(self, weights, config=None):
        config = config or PosterConfig()
        games = [Game(i + 1, f'Game {i}', value) for i, value in enumerate(weights)]
        items = group_games(games, config)
        self.assertEqual(sum(item.playtime_minutes for item in items), sum(weights))
        tiles = squarify(items, config.width, config.height)
        if not sum(weights):
            self.assertEqual(tiles, [])
            return
        area = config.width * config.height
        self.assertAlmostEqual(sum(w * h for _, x, y, w, h in tiles), area, places=5)
        for index, (item, x, y, w, h) in enumerate(tiles):
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
            self.assertGreaterEqual(x, -1e-7)
            self.assertGreaterEqual(y, -1e-7)
            self.assertLessEqual(x + w, config.width + 1e-7)
            self.assertLessEqual(y + h, config.height + 1e-7)
            self.assertAlmostEqual(w * h / area, item.playtime_minutes / sum(weights), places=11)
            for _, a, b, c, d in tiles[index + 1:]:
                self.assertTrue(min(x + w, a + c) - max(x, a) < 1e-7 or
                                min(y + h, b + d) - max(y, b) < 1e-7)

    def test_empty_single_equal_and_extreme_weights(self):
        for weights in ([], [0, 0], [1], [1]*30, [1_000_000_000, 1, 1], [300, 150, 50, 0]):
            self.check_geometry(weights)

    def test_random_area_conservation_and_non_overlap(self):
        rng = random.Random(7)
        for count in (5, 30, 200, 500):
            self.check_geometry([rng.randint(1, 1000000) for _ in range(count)])

    def test_top_n_preserves_other_minutes(self):
        games = [Game(i + 1, 'Game', 100 - i) for i in range(40)]
        items = group_games(games, PosterConfig(max_games=3))
        self.assertEqual(len(items), 4)
        other = next(item for item in items if item.is_group)
        self.assertEqual(len(other.games), 37)
        self.assertIsNone(other.app_id)
        self.check_geometry([g.playtime_minutes for g in games], PosterConfig(max_games=3))

    def test_tiny_games_remain_individual(self):
        games = [Game(1, 'Large', 1000000), Game(2, 'Tiny', 1)]
        items = group_games(games, PosterConfig())
        self.assertEqual(len(items), 2)
        self.assertFalse(any(item.is_group for item in items))

    def test_no_top_twelve_cutoff(self):
        games = [Game(i + 1, 'Game', 1) for i in range(2000)]
        items = group_games(games, PosterConfig())
        self.assertEqual(len(squarify(items, 1920, 1080)), 2000)

    def test_invalid_config(self):
        for config in (PosterConfig(max_games=-1), PosterConfig(width=0), PosterConfig(gap=20)):
            with self.assertRaises(ValueError):
                config.validate()


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 19, tzinfo=timezone.utc)

    def game(self, appid, days, minutes=60):
        timestamp = None if days is None else int((self.now - timedelta(days=days)).timestamp())
        return Game(appid, f'Game {appid}', minutes, last_played=timestamp)

    def test_recent_boundary_missing_dates_and_future(self):
        library = GameLibrary('Player', [self.game(1, 365), self.game(2, 366), self.game(3, 0),
                                        self.game(4, None), self.game(5, -1), self.game(6, 10, 0)])
        selected, note, unknown = select_library(library, 'recent_year', self.now)
        self.assertEqual([game.app_id for game in selected.games], [1, 3])
        self.assertEqual(unknown, 2)
        self.assertIn('NOT ANNUAL HOURS', note)
        self.assertIn('2 UNKNOWN', note)

    def test_all_missing_is_unavailable_not_empty(self):
        with self.assertRaisesRegex(ValueError, 'no usable'):
            select_library(GameLibrary('Player', [self.game(1, None)]), 'recent_year', self.now)

    def test_old_games_yield_valid_empty_selection(self):
        selected, note, unknown = select_library(GameLibrary('Player', [self.game(1, 700)]), 'recent_year', self.now)
        self.assertEqual(selected.total_games(), 0)
        self.assertEqual(unknown, 0)

    def test_lifetime_values_preserved_and_source_unchanged(self):
        library = GameLibrary('Player', [self.game(1, 1, 50000), self.game(2, 500, 100)])
        filtered, _, _ = select_library(library, 'recent_year', self.now)
        self.assertEqual(filtered.total_playtime_minutes(), 50000)
        self.assertEqual(library.total_games(), 2)
        self.assertIs(select_library(library, 'all')[0], library)

    def test_optional_fields_validate_without_fabricating_zero(self):
        game = Game(1, 'Game', 60, last_played='wrong', playtime_2weeks=-1)
        self.assertIsNone(game.last_played)
        self.assertIsNone(game.playtime_2weeks)


class DataAndRenderTests(unittest.TestCase):
    @patch('src.steam.steam_api.SteamClient._get')
    def test_api_optional_fields_and_missing_fields(self, get):
        get.side_effect = [{'response': {'games': [
            {'appid': 1, 'name': 'A', 'playtime_forever': 1000, 'rtime_last_played': 1789000000, 'playtime_2weeks': 33},
            {'appid': 2, 'name': 'B', 'playtime_forever': 500}]}}, {'response': {'players': []}}]
        library = SteamClient('test-only').load_library('76561198000000000')
        self.assertEqual(library.games[0].last_played, 1789000000)
        self.assertEqual(library.games[0].playtime_2weeks, 33)
        self.assertIsNone(library.games[1].last_played)

    @patch('src.steam.steam_api.urlopen', side_effect=URLError('offline'))
    def test_api_network_failure(self, request):
        with self.assertRaises(SteamError):
            SteamClient('test-only').load_library('76561198000000000')

    @patch('src.common.utils.urlopen', side_effect=AssertionError('Offline demo must not download'))
    def test_demo_all_and_recent(self, network):
        library = load_demo()
        self.assertEqual(library.total_playtime_minutes(), 98850)
        self.assertEqual(len(PosterRenderer(library).items), 12)
        self.assertEqual(PosterRenderer(library, mode='recent_year').library.total_games(), 8)
        network.assert_not_called()

    def test_png_svg_dimensions_and_corrupt_cache_fallback(self):
        library = GameLibrary('<Player & friends>', [Game(1, 'A very long name '*20, 30), Game(2, 'Other (a title)', 15)])
        with tempfile.TemporaryDirectory() as folder, patch('src.poster.image_renderer.ART_DIR', Path(folder)):
            (Path(folder)/'1_portrait.jpg').write_bytes(b'broken')
            poster = PosterRenderer(library, config=PosterConfig(orientation='landscape'))
            svg = Path(folder)/'poster.svg'
            poster.export_svg(svg)
            parsed = ET.parse(svg).getroot()
            self.assertEqual(parsed.attrib['width'], '1920')
            self.assertEqual(parsed.attrib['height'], '1080')
            self.assertIn('&lt;Player &amp;', svg.read_text(encoding='utf-8'))
            self.assertEqual(poster.items[1].app_id, 2)
            if Image is not None:
                self.assertIsNone(poster.cover_path(poster.items[0], 100, 100))
                png = Path(folder)/'poster.png'
                poster.export_png(png)
                with Image.open(png) as result:
                    self.assertEqual(result.size, (1920, 1080))

    @patch('src.common.utils.urlopen', side_effect=URLError('offline'))
    def test_cached_artwork_never_redownloads_and_missing_is_safe(self, network):
        with tempfile.TemporaryDirectory() as folder, patch('src.common.utils.ART_DIR', Path(folder)):
            for suffix in ('_portrait.jpg', '.jpg'):
                (Path(folder)/('1'+suffix)).write_bytes(b'existing cache')
            download_covers([Game(1, 'Cached', 1)])
            network.assert_not_called()
            download_covers([Game(2, 'Missing', 1)])
            self.assertEqual(network.call_count, 2)

    def test_other_and_small_tiles_support_hover(self):
        library = GameLibrary('Player', [Game(i + 1, 'Game', i + 1) for i in range(30)])
        poster = PosterRenderer(library, config=PosterConfig(max_games=4))
        for item, x, y, w, h in poster.tiles:
            self.assertIs(poster.tile_at(x + w/2, y + h/2), item)
        self.assertIsNone(poster.tile_at(-1, -1))


if __name__ == '__main__':
    unittest.main()
