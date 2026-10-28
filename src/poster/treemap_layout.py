"""Squarified treemap with exact weight preservation and optional Other aggregation."""

from dataclasses import dataclass


@dataclass
class PosterItem:
    """One actual game, or an explicitly labelled group of small games."""

    name: str
    games: list
    is_group: bool = False

    @property
    def playtime_minutes(self):
        return sum(game.playtime_minutes for game in self.games)

    @property
    def playtime_hours(self):
        return self.playtime_minutes / 60

    @property
    def app_id(self):
        return None if self.is_group else self.games[0].app_id


def group_games(games, config):
    """Group beyond-limit games without dropping any played minutes."""
    config.validate()
    ranked = sorted((g for g in games if g.playtime_minutes > 0),
                    key=lambda g: (-g.playtime_minutes, g.app_id))
    individual, other = [], []
    for index, game in enumerate(ranked):
        if config.max_games and index >= config.max_games:
            other.append(game)
        else:
            individual.append(PosterItem(game.name, [game]))
    if other:
        individual.append(PosterItem(f'Other ({len(other)} games)', other, True))
    return sorted(individual, key=lambda item: -item.playtime_minutes)


def squarify(items, width, height, weight=None):
    """Return (item, x, y, w, h) filling the complete canvas.

    Grow a row while adding the next item improves its worst aspect ratio,
    then place that row along the shorter side of the remaining rectangle.
    """
    if width <= 0 or height <= 0:
        raise ValueError('Treemap dimensions must be positive.')
    ranked = sorted((item for item in items if item.playtime_minutes > 0),
                    key=lambda item: -item.playtime_minutes)
    values = [weight(item) if weight else item.playtime_minutes for item in ranked]
    total = sum(values)
    if not total:
        return []
    areas = [value / total * width * height for value in values]
    x, y, remaining_w, remaining_h = 0.0, 0.0, float(width), float(height)
    tiles, index = [], 0

    def worst(row, short_side):
        area_sum = sum(row)
        return max(short_side**2 * max(row) / area_sum**2,
                   area_sum**2 / (short_side**2 * min(row)))

    while index < len(ranked):
        short = min(remaining_w, remaining_h)
        end = index + 1
        row = [areas[index]]
        while end < len(ranked) and worst(row + [areas[end]], short) <= worst(row, short):
            row.append(areas[end])
            end += 1
        row_area = sum(row)
        if remaining_w >= remaining_h:
            strip = remaining_w if end == len(ranked) else row_area / remaining_h
            offset = y
            for position in range(index, end):
                side = y + remaining_h - offset if position == end - 1 else areas[position] / strip
                tiles.append((ranked[position], x, offset, strip, side))
                offset += side
            x += strip
            remaining_w -= strip
        else:
            strip = remaining_h if end == len(ranked) else row_area / remaining_w
            offset = x
            for position in range(index, end):
                side = x + remaining_w - offset if position == end - 1 else areas[position] / strip
                tiles.append((ranked[position], offset, y, side, strip))
                offset += side
            y += strip
            remaining_h -= strip
        index = end
    return tiles


def layout_poster(items, config):
    """Reserve header/footer space; grow vertical artwork instead of shrinking games.

    Vertical weights have a readability floor (one ninth of the largest weight).
    This intentionally relaxes exact proportions; displayed shares remain exact.
    Landscape retains the original proportional geometry within its content area.
    """
    from math import ceil
    header, footer = 120, 80
    if config.orientation == 'landscape':
        # Keep the width fixed; scale changes tile area before arranging the treemap.
        # At 75% the original 1920 x 1080 default is retained.
        width = config.width
        content_height = ceil((config.height - header - footer) * (config.scale / .75)**2)
        tiles = squarify(items, width, content_height)
    else:
        width = config.vertical_width
        highest = max((item.playtime_minutes for item in items), default=1)
        def readable_weight(item):
            return max(1.0, 9 * item.playtime_minutes / highest)
        target_side = 250 * config.scale / .75
        content_height = ceil(max(width * config.scale / .75,
                                  sum(readable_weight(item) for item in items) * target_side**2 / width))
        tiles = squarify(items, width, content_height, readable_weight)
        minimum_edge = max(96, 160 * config.scale / .75)
        # Extra height also prevents short, wide slivers in uneven libraries.
        for attempt in range(30):
            if not tiles or min(min(w, h) for _, x, y, w, h in tiles) >= minimum_edge:
                break
            content_height = ceil(content_height * 1.1)
            tiles = squarify(items, width, content_height, readable_weight)
    return [(item, x, y + header, w, h) for item, x, y, w, h in tiles], width, content_height + header + footer
