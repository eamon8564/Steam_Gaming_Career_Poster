"""Poster defaults; grouping is also adjustable in the desktop window."""

from dataclasses import dataclass


@dataclass
class PosterConfig:
    """All areas are calculated before cosmetic gaps and labels."""

    width: int = 1920
    height: int = 1080
    gap: int = 3
    max_games: int = 0  # 0 means no top-N limit.
    orientation: str = 'vertical'
    scale: float = 0.75
    vertical_width: int = 1080

    def validate(self):
        """Reject invalid settings instead of silently altering the picture."""
        if self.orientation not in ('vertical', 'landscape'):
            raise ValueError('Orientation must be vertical or landscape.')
        if self.scale not in (1.0, 0.75, 0.65, 0.5, 0.4):
            raise ValueError('Select 100%, 75%, 65%, 50% or 40% density.')
        if type(self.vertical_width) is not int or not 640 <= self.vertical_width <= 2160:
            raise ValueError('Vertical width must be between 640 and 2160 pixels.')
        if type(self.width) is not int or type(self.height) is not int:
            raise ValueError('Image dimensions must be integers.')
        if not 640 <= self.width <= 7680 or not 360 <= self.height <= 4320:
            raise ValueError('Image dimensions must be between 640x360 and 7680x4320.')
        if type(self.max_games) is not int or self.max_games < 0:
            raise ValueError('Individual game limit must be an integer >= 0 (0 = all).')
        if not 0 <= self.gap <= 10:
            raise ValueError('Gap must be between 0 and 10 pixels.')
