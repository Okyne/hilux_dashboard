import math
import os
import tempfile
import unittest

import tire_calibration as tc


class TestCircumference(unittest.TestCase):
    def test_known_value_for_255_70_r15(self):
        diameter_mm = 15 * 25.4 + 2 * (255 * 70 / 100)
        expected = math.pi * diameter_mm
        self.assertAlmostEqual(tc.circumference_mm(255, 70, 15), expected, places=6)


class TestSpeedRatio(unittest.TestCase):
    def test_reference_size_has_ratio_one(self):
        self.assertAlmostEqual(tc.speed_ratio(255, 70, 15), 1.0, places=9)

    def test_bigger_tire_has_ratio_above_one(self):
        self.assertGreater(tc.speed_ratio(265, 70, 16), 1.0)

    def test_smaller_tire_has_ratio_below_one(self):
        self.assertLess(tc.speed_ratio(195, 60, 14), 1.0)


class TestSettingsPersistence(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tire_settings.json")
            tc.save_settings(265, 70, 16, path=path)
            self.assertEqual(
                tc.load_settings(path=path),
                {"width": 265.0, "aspect": 70.0, "rim": 16.0},
            )

    def test_missing_file_returns_reference(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "does_not_exist.json")
            self.assertEqual(tc.load_settings(path=path), tc.REFERENCE_TIRE)


if __name__ == "__main__":
    unittest.main()
