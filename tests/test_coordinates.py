"""
Automated Test Suite for Canvas Coordinate Translation
Validates the canonical screen-to-image coordinate mapping formulas.
"""

import unittest

def translate_coordinates(clientX, clientY, rect_left, rect_top, rect_width, rect_height, canvas_width, canvas_height):
    """
    Canonical coordinate translation formula.
    Maps screen space mouse/touch events to original image pixel coordinates.
    """
    if rect_width <= 0 or rect_height <= 0:
        return 0.0, 0.0
    x = (clientX - rect_left) * (canvas_width / rect_width)
    y = (clientY - rect_top) * (canvas_height / rect_height)
    return round(x, 2), round(y, 2)

class TestCoordinateTranslation(unittest.TestCase):
    def test_center_100_percent_zoom(self):
        # Image is 2000x1000, displayed at 1000x500
        # Clicked exactly in the center of the screen
        x, y = translate_coordinates(
            clientX=500, clientY=250,
            rect_left=0, rect_top=0, rect_width=1000, rect_height=500,
            canvas_width=2000, canvas_height=1000
        )
        self.assertEqual(x, 1000.0)
        self.assertEqual(y, 500.0)

    def test_zoom_200_percent(self):
        # Image is 2000x1000, displayed zoomed in at 2000x1000
        # Clicked at client position (400, 300)
        x, y = translate_coordinates(
            clientX=400, clientY=300,
            rect_left=0, rect_top=0, rect_width=2000, rect_height=1000,
            canvas_width=2000, canvas_height=1000
        )
        self.assertEqual(x, 400.0)
        self.assertEqual(y, 300.0)

    def test_zoom_50_percent(self):
        # Image is 2000x1000, displayed zoomed out at 500x250
        # Clicked at client position (250, 125)
        x, y = translate_coordinates(
            clientX=250, clientY=125,
            rect_left=0, rect_top=0, rect_width=500, rect_height=250,
            canvas_width=2000, canvas_height=1000
        )
        self.assertEqual(x, 1000.0)
        self.assertEqual(y, 500.0)

    def test_panned_offset(self):
        # Image is 2000x1000, displayed at 1000x500 with left offset (panned right) of 100px
        # Clicked at client position (600, 250)
        x, y = translate_coordinates(
            clientX=600, clientY=250,
            rect_left=100, rect_top=0, rect_width=1000, rect_height=500,
            canvas_width=2000, canvas_height=1000
        )
        self.assertEqual(x, 1000.0)
        self.assertEqual(y, 500.0)

    def test_portrait_aspect_ratio(self):
        # Image is 1000x2000 (portrait), displayed at 400x800
        # Clicked at client position (200, 400)
        x, y = translate_coordinates(
            clientX=200, clientY=400,
            rect_left=50, rect_top=50, rect_width=400, rect_height=800,
            canvas_width=1000, canvas_height=2000
        )
        self.assertEqual(x, 375.0)
        self.assertEqual(y, 875.0)

if __name__ == "__main__":
    unittest.main()
