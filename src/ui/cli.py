"""Offline command-line demonstration for environments without a GUI display."""

import argparse
from datetime import datetime
import sys

from src.common.paths import PROJECT_DIR
from src.common.utils import load_demo
from src.core.config import PosterConfig
from src.poster.image_renderer import PosterRenderer


def parse_options(argv=None):
    """Read optional terminal-demo settings; no arguments open the desktop GUI."""
    parser = argparse.ArgumentParser(description='Steam Gaming Career Poster: desktop GUI or offline terminal demo.')
    parser.add_argument('--no-gui', '--headless', action='store_true', help='Generate a demo poster without a display.')
    parser.add_argument('--format', choices=('svg', 'png'), default='svg', help='Terminal export format (default: svg).')
    parser.add_argument('--orientation', choices=('vertical', 'landscape'), default='vertical', help='Terminal poster orientation.')
    parser.add_argument('--scale', type=int, choices=(100, 75, 65, 50, 40), default=75, help='Terminal layout scale percentage.')
    parser.add_argument('--mode', choices=('all', 'recent_year'), default='all', help='Terminal library selection.')
    parser.add_argument('--top-n', type=int, default=0, help='Individual game limit; 0 means all.')
    return parser.parse_args(argv)


def run_demo(options):
    """Print fictional library statistics and export using the existing renderer."""
    try:
        config = PosterConfig(orientation=options.orientation, scale=options.scale / 100,
                              max_games=options.top_n)
        poster = PosterRenderer(load_demo(), mode=options.mode, config=config)
        output = PROJECT_DIR / 'output'
        output.mkdir(parents=True, exist_ok=True)
        name = ('demo_' + options.orientation + '_' + options.mode + '_' +
                datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.' + options.format)
        path = output / name
        if options.format == 'png':
            poster.export_png(path)
        else:
            poster.export_svg(path)
    except (OSError, ValueError) as error:
        print('Cannot generate the terminal demo: ' + str(error), file=sys.stderr)
        print('Keep data/, cache/ and src/ beside main.py. SVG needs no third-party libraries.', file=sys.stderr)
        return 1

    library = poster.library
    print('\nSTEAM GAMING CAREER POSTER | OFFLINE DEMO')
    print('Fictional statistics; no Steam login, key or network request is used.')
    print(f'Games in selection: {library.total_games()}')
    print(f'Played games: {len(library.played_games())}')
    print(f'Lifetime hours: {library.total_playtime_minutes() / 60:,.1f}')
    print(poster.scope_note)
    print('\nGames by lifetime playtime:')
    for game in library.top_games(limit=library.total_games()):
        share = game.playtime_minutes / library.total_playtime_minutes()
        print(f'  {game.name}: {game.playtime_hours:,.1f} h ({share:.1%})')
    print(f'\nPoster: {poster.width} x {poster.height} px')
    print('Saved: ' + str(path))
    print('Download the exported file to view it locally. SVG opens in a web browser.')
    print('For the interactive window, run this program on a computer with a graphical desktop.')
    return 0
