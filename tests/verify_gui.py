"""Real Tkinter smoke test with no account login or external networking."""

from pathlib import Path
import sys
import tempfile
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ui.app import GamingJourneyApp
from src.poster.image_renderer import Image
from src.core.models import Game, GameLibrary
from src.common.utils import PROJECT_DIR


def main():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    root = tk.Tk()
    errors = []
    root.report_callback_exception = lambda *details: errors.append(details)
    app = GamingJourneyApp(root)
    root.update()
    app.load_demo()
    root.update()
    assert app.builder.library.total_games() == 15
    app.mode.set('Played in last 365 days / recent_year')
    app.apply_settings()
    assert app.builder.library.total_games() == 8
    assert 'NOT ANNUAL' in app.builder.scope_note
    app.max_games.set('3')
    app.apply_settings()
    assert len(app.builder.items) == 4
    assert any(item.is_group for item in app.builder.items)
    app.mode.set('All games / all')
    app.max_games.set('0')
    app.apply_settings()
    assert app.builder.library.total_games() == 15
    app.max_games.set('invalid')
    with patch('src.ui.app.messagebox.showerror') as dialog:
        app.apply_settings()
        assert dialog.called
    assert app.max_games.get() == '0'
    assert not hasattr(app, 'min_area')
    assert not hasattr(app, 'achievement_borders')
    with tempfile.TemporaryDirectory(dir=PROJECT_DIR/'output', ignore_cleanup_errors=True) as folder:
        for extension in (['svg', 'png'] if Image is not None else ['svg']):
            path = Path(folder)/('poster.' + extension)
            with patch('src.ui.app.filedialog.asksaveasfilename', return_value=str(path)):
                app.export_button.invoke()
            assert path.is_file()
            if extension == 'png':
                with Image.open(path) as exported:
                    assert exported.size == (app.builder.width, app.builder.height)
    app.show_games()
    root.update()
    for child in root.winfo_children():
        if isinstance(child, tk.Toplevel):
            child.destroy()
    for size in ('980x600', '1360x960'):
        root.geometry(size)
        root.update()
        app.redraw()
        root.update()
        assert app.preview_width <= app.canvas.winfo_width() + 1
    assert app.orientation.get() == 'Vertical'
    assert app.poster_scale.get() == '75%'
    vertical_height = app.builder.height
    app.poster_scale.set('100%')
    app.apply_settings()
    assert app.builder.height > vertical_height
    app.canvas.yview_moveto(1)
    root.update()
    assert app.canvas.canvasy(0) > 0
    app.orientation.set('Landscape')
    app.apply_settings()
    assert app.builder.width == 1920
    assert app.builder.height > 1080
    app.poster_scale.set('75%')
    app.apply_settings()
    assert (app.builder.width, app.builder.height) == (1920, 1080)
    app.poster_scale.set('40%')
    app.apply_settings()
    assert app.builder.height < 1080
    app.orientation.set('Vertical')
    app.poster_scale.set('75%')
    app.apply_settings()
    if '--capture' in sys.argv and Image is not None:
        from capture_window import capture
        root.geometry('1360x960+20+20')
        root.attributes('-topmost', True)
        app.status.set('Vertical / 75% · Scroll for the complete career poster · Export PNG or SVG')
        root.update()
        root.after(800, root.quit)
        root.mainloop()
        capture(root, PROJECT_DIR/'output'/'app_vertical_settings.png')
    app.show_library(GameLibrary('Unknown dates', [Game(1, 'Game', 1)]), 'Test')
    app.mode.set('Played in last 365 days / recent_year')
    with patch('src.ui.app.messagebox.showerror'):
        app.apply_settings()
    assert app.mode.get() == 'All games / all'
    app.show_library(GameLibrary('Empty', []), 'Test')
    root.update()
    assert not app.builder.tiles
    app.close()
    assert not errors, errors
    print('GUI passed: all/recent filtering, grouping, invalid settings, full export, resize, missing dates, empty library.')


if __name__ == '__main__':
    main()
