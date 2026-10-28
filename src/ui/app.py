"""Tkinter controller. Network workers communicate through a queue, never Tk calls."""

from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from src.poster.image_renderer import BACKGROUND, WHITE, MUTED, ACCENT, PosterRenderer, Image
from src.core.config import PosterConfig
from src.steam.steam_api import SteamClient, SteamError, validate_steam_id
from src.steam.steam_auth import sign_in
from src.common.utils import PROJECT_DIR, download_covers, load_demo


class GamingJourneyApp:
    """Load a library, display its journey, and save a shareable image."""

    def __init__(self, root):
        self.root = root
        self.builder = None
        self.full_library = None
        self.library_source = "Demo / offline"
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.generation = 0
        self.busy = False
        self.redraw_job = None
        root.title("Steam Gaming Career Poster · Treemap")
        root.geometry("1240x860")
        root.minsize(980, 600)
        root.configure(bg=BACKGROUND)
        root.protocol("WM_DELETE_WINDOW", self.close)
        toolbar = tk.Frame(root, bg=BACKGROUND, padx=20, pady=16)
        toolbar.pack(fill="x")
        self._button(toolbar, "Use Demo Data", self.load_demo, ACCENT).pack(side="left", padx=(0, 8))
        self.connect_button = self._button(toolbar, "Connect Steam", self.connect)
        self.connect_button.pack(side="left", padx=4)
        self.id_button = self._button(toolbar, "Load SteamID", self.load_id)
        self.id_button.pack(side="left", padx=4)
        self.export_button = self._button(toolbar, "Export Image", self.export, ACCENT)
        self.export_button.pack(side="right")
        self.export_button.configure(state="disabled")
        options = tk.Frame(root, bg=BACKGROUND, padx=20)
        options.pack(fill="x")
        self.mode = tk.StringVar(value='All games / all')
        selector = ttk.Combobox(options, textvariable=self.mode, state='readonly', width=33,
                 values=('All games / all', 'Played in last 365 days / recent_year'))
        selector.pack(side='left')
        selector.bind('<<ComboboxSelected>>', self.apply_settings)
        filter_options = tk.Frame(root, bg=BACKGROUND, padx=20, pady=4)
        filter_options.pack(fill='x')
        tk.Label(filter_options, text='Top N (0=all)', bg=BACKGROUND, fg=MUTED).pack(side='left', padx=(12, 4))
        self.max_games = tk.StringVar(value='0')
        ttk.Entry(filter_options, textvariable=self.max_games, width=6).pack(side='left')
        self._button(filter_options, 'Apply', self.apply_settings).pack(side='left', padx=8)
        self._button(options, 'Game list', self.show_games).pack(side='right')
        self._button(options, 'Mode info', self.year_info).pack(side='right', padx=4)
        poster_options = tk.Frame(root, bg=BACKGROUND, padx=20, pady=8)
        poster_options.pack(fill='x')
        tk.Label(poster_options, text='Orientation', bg=BACKGROUND, fg=MUTED,
                 font=('Segoe UI', -13)).pack(side='left')
        self.orientation = tk.StringVar(value='Vertical')
        orientation_box = ttk.Combobox(poster_options, textvariable=self.orientation,
                                      values=('Vertical', 'Landscape'), state='readonly', width=12)
        orientation_box.pack(side='left', padx=8)
        orientation_box.bind('<<ComboboxSelected>>', self.apply_settings)
        tk.Label(poster_options, text='Scale', bg=BACKGROUND, fg=MUTED,
                 font=('Segoe UI', -13)).pack(side='left', padx=(12, 4))
        self.poster_scale = tk.StringVar(value='75%')
        scale_box = ttk.Combobox(poster_options, textvariable=self.poster_scale,
                                values=('100%', '75%', '65%', '50%', '40%'), state='readonly', width=8)
        scale_box.pack(side='left', padx=8)
        scale_box.bind('<<ComboboxSelected>>', self.apply_settings)
        self.status = tk.StringVar(value="Ready · Choose Demo Data for an offline preview, or connect your Steam account.")
        tk.Label(root, textvariable=self.status, bg=BACKGROUND, fg=MUTED,
                 anchor="w", wraplength=700, padx=22, pady=5,
                 font=("Segoe UI", -13)).pack(fill="x")
        frame = tk.Frame(root, bg=BACKGROUND)
        frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.canvas = tk.Canvas(frame, bg=BACKGROUND, highlightthickness=0, yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.canvas.yview)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.preview_width = 1
        self.canvas.bind("<Motion>", self.hover_tile)
        self.canvas.bind("<Configure>", self.schedule_redraw)
        self.canvas.bind("<MouseWheel>", self.scroll)
        self.canvas.bind("<Button-4>", lambda event: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind("<Button-5>", lambda event: self.canvas.yview_scroll(3, "units"))
        self.canvas.create_text(50, 80, anchor="nw", text="Your library. Your story.",
                                fill=WHITE, font=("Segoe UI", -30, "bold"))
        self.canvas.create_text(50, 145, anchor="nw", width=620,
                                text="Vertical career poster: fixed width, automatic height, readable game covers.\n\n"
                                     "Use Demo Data to explore the complete experience offline.\n"
                                     "Steam sign-in opens the official website in your browser.",
                                fill=MUTED, font=("Segoe UI", -14))
        self.poll_job = root.after(100, self.poll_events)

    def _button(self, parent, text, command, color="#233243"):
        return tk.Button(parent, text=text, command=command, bg=color,
                         fg=BACKGROUND if color == ACCENT else WHITE,
                         activebackground="#76c990", relief="flat", cursor="hand2",
                         font=("Segoe UI", -14, "bold"), padx=14, pady=10)

    def scroll(self, event):
        """Scroll the collage with a mouse wheel or trackpad."""
        direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction * max(1, abs(event.delta) // 120) * 3, "units")

    def schedule_redraw(self, event=None):
        """Debounce resizing so image resampling does not happen on every pixel."""
        if self.redraw_job is not None:
            self.root.after_cancel(self.redraw_job)
        self.redraw_job = self.root.after(100, self.redraw)

    def redraw(self):
        """Fit the width while keeping a scrollable full-height image."""
        self.redraw_job = None
        if self.builder:
            self.preview_width = max(1, self.canvas.winfo_width())
            if self.builder.config.orientation == 'landscape':
                self.preview_width = max(1, min(self.preview_width,
                    self.canvas.winfo_height() * self.builder.width / self.builder.height))
            self.builder.draw_canvas(self.canvas, self.preview_width)

    def apply_settings(self, event=None):
        """Rebuild from the original library, so changing filters never loses data."""
        if self.full_library is None:
            return
        try:
            settings = PosterConfig(max_games=int(self.max_games.get()),
                                    orientation=self.orientation.get().lower(),
                                    scale=float(self.poster_scale.get().rstrip('%')) / 100)
            mode = 'recent_year' if 'recent_year' in self.mode.get() else 'all'
            builder = PosterRenderer(self.full_library, self.library_source, mode, settings)
        except ValueError as error:
            messagebox.showerror('Cannot apply settings', str(error), parent=self.root)
            if self.builder:
                self.mode.set('All games / all' if self.builder.mode == 'all' else 'Played in last 365 days / recent_year')
                self.max_games.set(str(self.builder.config.max_games))
                self.orientation.set(self.builder.config.orientation.title())
                self.poster_scale.set(f'{self.builder.config.scale:.0%}')
            return
        self.builder = builder
        self.export_button.configure(state='normal')
        self.status.set(f'{builder.width} × {builder.height} px · ' + builder.scope_note)
        self.redraw()
        self.canvas.yview_moveto(0)

    def hover_tile(self, event):
        """Reveal full game names and exact shares even when tiles cannot fit text."""
        if self.builder:
            scale = self.preview_width / self.builder.width
            game = self.builder.tile_at(self.canvas.canvasx(event.x) / scale,
                                        self.canvas.canvasy(event.y) / scale)
            if game:
                total = self.builder.library.total_playtime_minutes()
                self.status.set(f"{game.name} · {game.playtime_hours:,.2f} h · {game.playtime_minutes / total:.3%}")

    def year_info(self):
        """Explain the data limit without presenting lifetime values as annual playtime."""
        messagebox.showinfo('Poster modes',
            'All: all owned games; positive lifetime minutes determine area.\n\n'
            'Recent year: games whose last-played date falls within the last 365 days. '
            'Their LIFETIME hours determine area, NOT hours played during that year. '
            'Unknown dates are excluded and reported; if all dates are missing the mode is unavailable.\n\n'
            'Top N = 0 displays every played game separately. '
            'Top N > 0 groups remaining games into Other without losing playtime.', parent=self.root)

    def show_games(self):
        """List every owned game, including zero-time games and very small tiles."""
        if self.builder is None:
            messagebox.showinfo("Game list", "Load a library first.", parent=self.root)
            return
        window = tk.Toplevel(self.root)
        window.title("All owned games · lifetime playtime")
        window.geometry("800x520")
        table = ttk.Treeview(window, columns=("name", "hours", "share", "recent", "last"), show="headings")
        for column, title, width in (("name", "Game", 300), ("hours", "Lifetime h", 100), ("share", "Share", 90), ("recent", "Last 2 weeks h", 110), ("last", "Last played (UTC)", 150)):
            table.heading(column, text=title)
            table.column(column, width=width)
        bar = ttk.Scrollbar(window, command=table.yview)
        bar.pack(side="right", fill="y")
        table.configure(yscrollcommand=bar.set)
        table.pack(fill="both", expand=True)
        library = self.builder.library
        total = library.total_playtime_minutes()
        for game in sorted(library.games, key=lambda item: (-item.playtime_minutes, item.app_id)):
            share = game.playtime_minutes / total if total else 0
            recent = 'Unavailable' if game.playtime_2weeks is None else f'{game.playtime_2weeks / 60:.2f}'
            from datetime import timezone
            try:
                last = datetime.fromtimestamp(game.last_played, timezone.utc).strftime('%Y-%m-%d') if game.last_played else 'Unknown'
            except (ValueError, OSError, OverflowError):
                last = 'Unknown'
            table.insert('', 'end', values=(game.name, f'{game.playtime_hours:,.2f}', f'{share:.3%}', recent, last))

    def set_busy(self, busy):
        """Keep Demo Mode usable while Steam is loading or awaiting login."""
        self.busy = busy
        for button in (self.connect_button, self.id_button):
            button.configure(state="disabled" if busy else "normal")

    def load_demo(self):
        """Cancel pending live work and load the bundled data without network access."""
        self.cancel.set()
        self.generation += 1
        self.set_busy(False)
        try:
            self.show_library(load_demo(), "Demo / offline")
            self.status.set("Demo loaded · Fictional playtimes and activity dates · Hover tiles or open Game list.")
        except ValueError as error:
            self.status.set(str(error))
            messagebox.showerror("Demo data unavailable", str(error), parent=self.root)

    def show_library(self, library, source):
        """Use the same analysis and drawing path for both data sources."""
        self.full_library, self.library_source = library, source
        self.builder = None
        self.export_button.configure(state='disabled')
        self.canvas.delete('all')
        self.apply_settings()
        if self.builder is None:
            # A newly loaded account must not leave the previous account's poster on screen.
            self.mode.set('All games / all')
            self.max_games.set('0')
            self.apply_settings()

    def connect(self):
        """Start official browser sign-in after checking local API configuration."""
        self.start_live()

    def load_id(self):
        """Allow manual SteamID64 loading as an alternative to browser sign-in."""
        steam_id = simpledialog.askstring("Load Steam library", "SteamID64 (17 digits):", parent=self.root)
        if steam_id:
            self.start_live(steam_id.strip())

    def start_live(self, steam_id=None):
        """Run authentication, API and optional artwork loading off the UI thread."""
        if self.busy:
            return
        try:
            client = SteamClient()
            if steam_id is not None:
                validate_steam_id(steam_id)
        except SteamError as error:
            self.live_error(str(error))
            return
        self.cancel.set()
        self.cancel = threading.Event()
        cancel = self.cancel
        self.generation += 1
        generation = self.generation
        self.set_busy(True)
        self.status.set("Loading Steam… Complete sign-in in your browser. Use Demo Data to cancel."
                        if steam_id is None else "Loading Steam library… Use Demo Data to cancel.")

        def worker():
            try:
                identity = steam_id if steam_id is not None else sign_in(cancel)
                if cancel.is_set():
                    return
                library = client.load_library(identity)
                if cancel.is_set():
                    return
                self.events.put((generation, "library", library))
                if Image is not None:
                    games = library.top_games(library.total_games())
                    for start in range(0, len(games), 12):
                        if cancel.is_set():
                            return
                        download_covers(games[start:start + 12], cancel)
                        self.events.put((generation, "progress", min(start + 12, len(games))))
                self.events.put((generation, "artwork", None))
            except (SteamError, OSError) as error:
                message = str(error) if isinstance(error, SteamError) else "Steam connection failed. Please try again."
                self.events.put((generation, "error", message))

        threading.Thread(target=worker, daemon=True).start()

    def live_error(self, message):
        """Explain failures and offer the complete offline experience."""
        self.set_busy(False)
        self.status.set(message)
        if messagebox.askyesno("Steam unavailable", message + "\n\nLoad Demo Mode instead?", parent=self.root):
            self.load_demo()

    def poll_events(self):
        """Apply only results from the current request, on Tkinter's main thread."""
        try:
            while True:
                generation, kind, value = self.events.get_nowait()
                if generation != self.generation:
                    continue
                if kind == "error":
                    self.live_error(value)
                elif kind == "library":
                    self.show_library(value, "Steam / live")
                    self.status.set("Steam library loaded · Preparing artwork…" if value.games
                                    else "Steam returned an empty library. Demo Mode is available.")
                elif kind == "progress":
                    self.redraw()
                    self.status.set(f"Preparing artwork: {value} games checked. You can already save the collage.")
                else:
                    self.set_busy(False)
                    self.redraw()
                    self.status.set("Steam library ready · Missing artwork uses a coloured placeholder.")
        except queue.Empty:
            pass
        self.poll_job = self.root.after(100, self.poll_events)

    def export(self):
        """Save through a standard file dialog; no screenshot or remote upload needed."""
        if self.builder is None:
            return
        output = PROJECT_DIR / "output"
        try:
            output.mkdir(exist_ok=True)
            types = [("SVG image", "*.svg")]
            if Image is not None:
                types.insert(0, ("PNG image", "*.png"))
            extension = ".png" if Image is not None else ".svg"
            path = filedialog.asksaveasfilename(parent=self.root, title="导出完整生涯图片 / Export full image",
                      initialdir=output, initialfile="steam_career_" + self.builder.config.orientation + "_" + str(round(self.builder.config.scale * 100)) + "_" + self.builder.mode + "_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + extension,
                      defaultextension=extension, filetypes=types)
            if not path:
                return
            if not Path(path).resolve().is_relative_to(output.resolve()):
                raise ValueError('Please save inside career_poster/output/. Earlier outputs are preserved.')
            if Path(path).suffix.lower() == ".svg":
                self.builder.export_svg(path)
            elif Path(path).suffix.lower() == ".png":
                self.builder.export_png(path)
            else:
                raise ValueError("Choose a .png or .svg filename.")
            self.status.set(f"Saved: {path}")
        except (OSError, ValueError, MemoryError) as error:
            messagebox.showerror("Could not save image", str(error), parent=self.root)

    def close(self):
        """Stop pending work and release the window cleanly."""
        self.cancel.set()
        self.root.after_cancel(self.poll_job)
        if self.redraw_job is not None:
            self.root.after_cancel(self.redraw_job)
        self.root.destroy()
