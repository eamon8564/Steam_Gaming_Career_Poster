"""One simple drawing layout, shared by Tkinter, SVG and optional PNG output."""

import base64
from html import escape
from pathlib import Path
import unicodedata
from src.core.config import PosterConfig
from src.poster.treemap_layout import group_games, layout_poster
from src.steam.steam_data import select_library
import math

WIDTH = 1920

from src.core.analyzer import JourneyAnalyzer
from src.common.utils import ART_DIR

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
except ImportError:
    Image = None


BACKGROUND = "#0c121c"
WHITE = "#f4f5f7"
MUTED = "#9aabba"
ACCENT = "#a7edb0"
PALETTE = ("#284c5b", "#563635", "#494630", "#593b36", "#41445b", "#315346",
           "#493e58", "#3e5363", "#385643", "#533447", "#304d59", "#3e4c66")


def short_text(value, limit):
    """Keep unusually long player or game names inside their allocated space."""
    value = " ".join(str(value).split())
    return value if len(value) <= limit else value[:limit - 1] + "…"


def fit_text(value, width, size):
    """Conservative width estimate, including full-width CJK characters."""
    value = ' '.join(str(value).split())
    used = 0
    output = ''
    for char in value:
        cost = size if unicodedata.east_asian_width(char) in ('W', 'F') else size * .72
        if used + cost > width - size:
            return output + '…'
        output += char
        used += cost
    return output


class PosterRenderer:
    """Full-bleed squarified mosaic; PNG/SVG and preview share the same geometry."""

    def __init__(self, library, source='Demo / offline', mode='all', config=None, now=None):
        self.original_library = library
        self.library, self.scope_note, self.unknown_dates = select_library(library, mode, now)
        self.config = config or PosterConfig()
        self.config.validate()
        self.source, self.mode = source, mode
        self.cover_mode = 'crop'
        self.items = group_games(self.library.games, self.config)
        self.tiles, self.width, self.height = layout_poster(self.items, self.config)

    def tile_at(self, x, y):
        """Find a game or Other group under a pointer in image coordinates."""
        for item, left, top, width, height in self.tiles:
            if left <= x < left + width and top <= y < top + height:
                return item
        return None

    def cover_path(self, item, width, height):
        """Choose the cached source aspect ratio closest to the destination."""
        if item.app_id is None:
            return None
        choices = []
        for suffix, ratio in (('_portrait.jpg', 2 / 3), ('.jpg', 460 / 215), ('.png', 1)):
            path = ART_DIR / f'{item.app_id}{suffix}'
            if not path.is_file():
                continue
            if Image is not None:
                try:
                    with Image.open(path) as source:
                        source.verify()
                    with Image.open(path) as source:
                        ratio = source.width / source.height
                except (OSError, ValueError):
                    continue
            choices.append((abs(math.log((width / height) / ratio)), path))
        return min(choices, key=lambda pair: pair[0])[1] if choices else None

    def build_summary(self):
        """Fill the complete canvas with cover images; add compact title overlays."""
        scene = []
        def rect(x, y, w, h, color):
            if w > 0 and h > 0:
                scene.append(('rect', x, y, w, h, color))
        def text(x, y, value, size=14, color=WHITE, bold=False):
            scene.append(('text', x, y, str(value), size, color, bold))
        rect(0, 0, self.width, self.height, BACKGROUND)
        total = self.library.total_playtime_minutes()
        for index, (item, left, top, width, height) in enumerate(self.tiles):
            # Inset decoration only; the allocation keeps exactly the data's area ratio.
            inset = min(self.config.gap / 2, width / 8, height / 8)
            x, y, w, h = left + inset, top + inset, width - 2 * inset, height - 2 * inset
            rect(x, y, w, h, PALETTE[index % len(PALETTE)])
            cover = self.cover_path(item, w, h)
            if cover:
                scene.append(('image', x, y, w, h, cover))
            bottom = y + h
            label_space = h
            if w >= 100 and label_space >= 85:
                size = 34 if w * h > 220000 else (24 if w >= 300 else 15)
                band = size + 39
                rect(x, bottom - band, w, band, '#101a25')
                text(x + 10, bottom - band + 5, fit_text(item.name, w - 20, size), size, WHITE, True)
                text(x + 10, bottom - 24, fit_text(f'{item.playtime_hours:,.1f} h  /  {item.playtime_minutes / total:.1%}', w - 20, 13), 13, ACCENT)
            elif w >= 55 and label_space >= 28:
                rect(x, bottom - 24, w, 24, '#101a25')
                text(x + 4, bottom - 21, fit_text(item.name, w - 8, 12), 12, WHITE, True)
        if not self.tiles:
            text(60, self.height / 2 - 30, 'No games with recorded playtime in this selection.', 28, WHITE, True)
        rect(0, 0, self.width, 120, BACKGROUND)
        text(24, 18, 'STEAM / GAMING CAREER', 13, ACCENT, True)
        text(24, 47, fit_text(self.library.owner_name, self.width * .51, 28), 28, WHITE, True)
        text(self.width * .58, 47, f'{total / 60:,.1f} HOURS', 25, WHITE, True)
        text(self.width * .58, 85, f'{len(self.library.games)} GAMES / {self.source}', 13, MUTED)
        text(24, 87, f'{self.config.orientation.upper()} / {self.config.scale:.0%} DENSITY', 12, MUTED)
        rect(0, self.height - 80, self.width, 80, BACKGROUND)
        text(16, self.height - 66, fit_text(self.scope_note, self.width - 32, 11), 11, MUTED)
        detail = ('Readable tile sizes; percentages are actual lifetime shares.'
                  if self.config.orientation == 'vertical' else 'Tile areas follow lifetime playtime shares.')
        text(16, self.height - 40, detail, 12, MUTED)
        text(self.width - 200, self.height - 20, f'{self.width} x {self.height} px', 11, ACCENT)
        return scene

    def resize_cover(self, original, size):
        """Preserve source aspect ratio using high-quality crop or letterboxing."""
        original = original.convert('RGB')
        if self.cover_mode == 'contain':
            return ImageOps.pad(original, size, method=Image.Resampling.LANCZOS, color=BACKGROUND)
        return ImageOps.fit(original, size, method=Image.Resampling.LANCZOS)

    def draw_canvas(self, canvas, width):
        """Draw on Tkinter; keep image references alive to prevent blank tiles."""
        scale = width / self.width
        canvas.delete("all")
        canvas.configure(scrollregion=(0, 0, width, self.height * scale))
        canvas.cover_images = []
        for item in self.build_summary():
            kind, x, y = item[:3]
            if kind == "rect":
                _, x, y, w, h, color = item
                canvas.create_rectangle(x * scale, y * scale, (x + w) * scale,
                                        (y + h) * scale, fill=color, outline="")
            elif kind == "text":
                _, x, y, value, size, color, bold = item
                canvas.create_text(x * scale, y * scale, text=value, anchor="nw", fill=color,
                                   font=("Segoe UI", -max(1, round(size * scale)),
                                         "bold" if bold else "normal"))
            elif Image is not None:
                _, x, y, w, h, path = item
                try:
                    with Image.open(path) as original:
                        cover = self.resize_cover(original, (max(1, round(w * scale)), max(1, round(h * scale))))
                    photo = ImageTk.PhotoImage(cover, master=canvas)
                    canvas.cover_images.append(photo)
                    canvas.create_image(x * scale, y * scale, image=photo, anchor="nw")
                except (OSError, ValueError):
                    pass

    def export_svg(self, path):
        """Write a self-contained vector image with embedded artwork; standard library only."""
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
                 f'viewBox="0 0 {self.width} {self.height}">']
        for item in self.build_summary():
            kind, x, y = item[:3]
            if kind == "rect":
                _, x, y, w, h, color = item
                parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
            elif kind == "text":
                _, x, y, value, size, color, bold = item
                # XML excludes most ASCII control characters, even after escaping.
                value = "".join(char for char in value if ord(char) >= 32)
                parts.append(f'<text x="{x}" y="{y + size}" font-family="Segoe UI,Arial,sans-serif" '
                             f'font-size="{size}" font-weight="{700 if bold else 400}" '
                             f'fill="{color}">{escape(value)}</text>')
            else:
                _, x, y, w, h, cover = item
                try:
                    encoded = base64.b64encode(cover.read_bytes()).decode("ascii")
                    mime = "image/png" if cover.suffix == ".png" else "image/jpeg"
                    parts.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" '
                                 f'viewBox="0 0 {w} {h}" overflow="hidden"><image width="{w}" '
                                 f'height="{h}" preserveAspectRatio="xMidYMid {"meet" if self.cover_mode == "contain" else "slice"}" '
                                 f'href="data:{mime};base64,{encoded}"/></svg>')
                except OSError:
                    pass
        parts.append("</svg>")
        Path(path).write_text("\n".join(parts), encoding="utf-8")

    def export_png(self, path):
        """Save a crisp PNG if optional Pillow is installed."""
        if Image is None:
            raise ValueError("PNG export needs Pillow. SVG export works without extra libraries.")
        if self.width * self.height > 120_000_000:
            raise ValueError('This library is too large for a single PNG in memory. Export SVG for the complete image.')
        output = Image.new("RGB", (self.width, self.height), BACKGROUND)
        draw = ImageDraw.Draw(output)
        for item in self.build_summary():
            kind, x, y = item[:3]
            if kind == "rect":
                _, x, y, w, h, color = item
                left, top = round(x), round(y)
                right, bottom = round(x + w), round(y + h)
                if right > left and bottom > top:
                    draw.rectangle((left, top, right - 1, bottom - 1), fill=color)
            elif kind == "text":
                _, x, y, value, size, color, bold = item
                font = None
                names = (["C:/Windows/Fonts/seguisb.ttf", "DejaVuSans-Bold.ttf"] if bold
                         else ["C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf"])
                for name in names:
                    try:
                        font = ImageFont.truetype(name, size)
                        break
                    except OSError:
                        continue
                if font is None:
                    font = ImageFont.load_default()
                draw.text((x, y), value, fill=color, font=font, anchor="lt")
            else:
                _, x, y, w, h, cover = item
                try:
                    with Image.open(cover) as original:
                        left, top = round(x), round(y)
                        right, bottom = round(x + w), round(y + h)
                        if right > left and bottom > top:
                            output.paste(self.resize_cover(original, (right - left, bottom - top)), (left, top))
                except (OSError, ValueError):
                    pass
        output.save(path, "PNG")
