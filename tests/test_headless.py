"""No-display entry, command-line settings and standard-library export checks."""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ui.cli import parse_options, run_demo


def entry_module():
    spec = importlib.util.spec_from_file_location('poster_entry_for_test', ROOT / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HeadlessTests(unittest.TestCase):
    def test_explicit_headless_never_opens_tk_or_downloads(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tk = types.SimpleNamespace(Tk=Mock(side_effect=AssertionError('No GUI allowed')))
            with patch.dict(sys.modules, {'tkinter': tk}), patch('src.ui.cli.PROJECT_DIR', root):
                with patch('src.common.utils.urlopen', side_effect=AssertionError('No network allowed')):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(entry_module().main(['--no-gui']), 0)
            tk.Tk.assert_not_called()
            files = list((root / 'output').glob('*.svg'))
            self.assertEqual(len(files), 1)
            self.assertEqual(ET.parse(files[0]).getroot().tag, '{http://www.w3.org/2000/svg}svg')
            self.assertIn('1,647.5', output.getvalue())

    def test_no_display_automatically_uses_demo(self):
        class DisplayError(Exception):
            pass
        tk = types.SimpleNamespace(TclError=DisplayError, Tk=Mock(side_effect=DisplayError('no display name')))
        with patch.dict(sys.modules, {'tkinter': tk}), patch('src.ui.cli.run_demo', return_value=0) as demo:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(entry_module().main([]), 0)
            demo.assert_called_once()

    def test_missing_tkinter_automatically_uses_demo(self):
        with patch.dict(sys.modules, {'tkinter': None}), patch('src.ui.cli.run_demo', return_value=0) as demo:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(entry_module().main([]), 0)
            demo.assert_called_once()

    def test_landscape_options_and_invalid_settings(self):
        with tempfile.TemporaryDirectory() as folder, patch('src.ui.cli.PROJECT_DIR', Path(folder)):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_demo(parse_options(['--no-gui', '--orientation', 'landscape', '--scale', '50', '--top-n', '3'])), 0)
            root = ET.parse(next((Path(folder) / 'output').glob('*.svg'))).getroot()
            self.assertEqual(root.attrib['width'], '1920')
            self.assertLess(int(root.attrib['height']), 1080)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(run_demo(parse_options(['--no-gui', '--top-n', '-1'])), 1)

    def test_png_without_pillow_returns_a_useful_error(self):
        with tempfile.TemporaryDirectory() as folder, patch('src.ui.cli.PROJECT_DIR', Path(folder)):
            error = io.StringIO()
            with patch('src.poster.image_renderer.Image', None), contextlib.redirect_stderr(error):
                self.assertEqual(run_demo(parse_options(['--no-gui', '--format', 'png'])), 1)
            self.assertIn('SVG', error.getvalue())


if __name__ == '__main__':
    unittest.main()
