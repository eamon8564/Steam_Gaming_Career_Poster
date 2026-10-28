"""Vertical geometry, layout density and image-aspect regression checks."""

from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core.config import PosterConfig
from src.poster.image_renderer import PosterRenderer, Image
from src.core.models import Game, GameLibrary


def library(count):
    return GameLibrary('Test player', [Game(i+1, f'Game {i}', max(1, 100000//(i+1)**2)) for i in range(count)])


class VerticalTests(unittest.TestCase):
    def test_defaults_and_monotonic_density(self):
        self.assertEqual(PosterConfig().orientation, 'vertical')
        self.assertEqual(PosterConfig().scale, .75)
        for count in (1, 12, 50, 200):
            heights = []
            for scale in (.4, .5, .65, .75, 1):
                poster = PosterRenderer(library(count), config=PosterConfig(scale=scale))
                self.assertEqual(poster.width, 1080)
                self.assertEqual(len(poster.tiles), count)
                self.assertGreaterEqual(min(min(t[3:]) for t in poster.tiles), max(96,160*scale/.75)-1e-6)
                heights.append(poster.height)
            self.assertEqual(heights, sorted(set(heights)))

    def test_more_games_grow_height_and_preserve_layout_bounds(self):
        heights = []
        for count in (12, 50, 200):
            poster = PosterRenderer(library(count), config=PosterConfig())
            heights.append(poster.height)
            self.assertAlmostEqual(sum(w*h for _,x,y,w,h in poster.tiles), poster.width*(poster.height-200), places=4)
            for i, (_,x,y,w,h) in enumerate(poster.tiles):
                self.assertGreaterEqual(y,120)
                self.assertLessEqual(y+h,poster.height-80+1e-6)
                for _,a,b,c,d in poster.tiles[i+1:]:
                    self.assertTrue(min(x+w,a+c)-max(x,a)<1e-6 or min(y+h,b+d)-max(y,b)<1e-6)
        self.assertEqual(heights,sorted(set(heights)))

    def test_landscape_preserves_true_area_shares(self):
        poster=PosterRenderer(library(20),config=PosterConfig(orientation='landscape'))
        self.assertEqual((poster.width,poster.height),(1920,1080))
        total=poster.library.total_playtime_minutes()
        for item,x,y,w,h in poster.tiles:
            self.assertAlmostEqual(w*h/(1920*880),item.playtime_minutes/total,places=10)

    def test_landscape_density_changes_layout_and_exports(self):
        import tempfile
        import xml.etree.ElementTree as ET
        heights = []
        for scale in (.4, .5, .65, .75, 1):
            poster = PosterRenderer(library(20), config=PosterConfig(orientation='landscape', scale=scale))
            heights.append(poster.height)
            self.assertEqual(poster.width, 1920)
            area = poster.width * (poster.height - 200)
            total = poster.library.total_playtime_minutes()
            self.assertEqual(len(poster.tiles), 20)
            self.assertAlmostEqual(sum(w*h for _,x,y,w,h in poster.tiles), area, places=5)
            for item,x,y,w,h in poster.tiles:
                self.assertGreaterEqual(y, 120)
                self.assertLessEqual(y+h, poster.height-80+1e-6)
                self.assertAlmostEqual(w*h/area, item.playtime_minutes/total, places=10)
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/'scaled.svg'
                poster.export_svg(path)
                self.assertEqual(int(ET.parse(path).getroot().attrib['height']), poster.height)
                if Image is not None:
                    path = Path(folder)/'scaled.png'
                    poster.export_png(path)
                    with Image.open(path) as result:
                        self.assertEqual(result.size, (poster.width, poster.height))
        self.assertEqual(heights, sorted(set(heights)))

    @unittest.skipIf(Image is None,'Pillow optional')
    def test_cover_never_squashes_circle(self):
        from PIL import ImageDraw
        source=Image.new('RGB',(800,400),'black')
        ImageDraw.Draw(source).ellipse((340,140,460,260),fill='white')
        poster=PosterRenderer(library(1))
        for size in ((200,400),(400,200),(224,224)):
            cover=poster.resize_cover(source,size)
            self.assertEqual(cover.size,size)
            mask=cover.convert('L').point(lambda value:255 if value>128 else 0)
            left,top,right,bottom=mask.getbbox()
            self.assertLessEqual(abs((right-left)-(bottom-top)),1)

    def test_invalid_orientation_and_scale(self):
        for settings in (PosterConfig(orientation='bad'),PosterConfig(scale=0),PosterConfig(vertical_width=0)):
            with self.assertRaises(ValueError):
                settings.validate()


if __name__=='__main__':
    unittest.main()
