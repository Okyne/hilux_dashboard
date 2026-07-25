import unittest

import theme


REQUIRED_KEYS = {
    "bg", "surface", "text", "text_dim", "accent",
    "ok", "warn", "alarm", "topbar", "topbar_tx",
}


class TestPaletteShape(unittest.TestCase):
    def test_day_and_night_have_required_keys(self):
        self.assertEqual(set(theme.DAY.keys()), REQUIRED_KEYS)
        self.assertEqual(set(theme.NIGHT.keys()), REQUIRED_KEYS)

    def test_all_values_are_rgba_tuples_in_range(self):
        for palette_name in ("DAY", "NIGHT"):
            palette_dict = getattr(theme, palette_name)
            for key, rgba in palette_dict.items():
                self.assertEqual(len(rgba), 4, f"{palette_name}.{key}")
                for channel in rgba:
                    self.assertGreaterEqual(channel, 0.0, f"{palette_name}.{key}")
                    self.assertLessEqual(channel, 1.0, f"{palette_name}.{key}")
                self.assertEqual(rgba[3], 1, f"{palette_name}.{key} alpha")


class TestPaletteFunction(unittest.TestCase):
    def test_palette_true_returns_night(self):
        self.assertIs(theme.palette(True), theme.NIGHT)

    def test_palette_false_returns_day(self):
        self.assertIs(theme.palette(False), theme.DAY)


class TestNightSeverityHierarchy(unittest.TestCase):
    def test_alarm_more_salient_than_warn_more_than_ok(self):
        alarm_max = max(theme.NIGHT["alarm"][:3])
        warn_max = max(theme.NIGHT["warn"][:3])
        ok_max = max(theme.NIGHT["ok"][:3])
        self.assertGreater(alarm_max, warn_max)
        self.assertGreater(warn_max, ok_max)

    def test_night_values_are_dimmer_than_day_for_alert_colors(self):
        for key in ("ok", "warn", "alarm"):
            self.assertLess(max(theme.NIGHT[key][:3]), max(theme.DAY[key][:3]))


class TestDayMatchesCurrentConstants(unittest.TestCase):
    def test_day_alert_colors_unchanged(self):
        self.assertEqual(theme.DAY["ok"], (0.16, 0.65, 0.34, 1))
        self.assertEqual(theme.DAY["warn"], (0.90, 0.60, 0.10, 1))
        self.assertEqual(theme.DAY["alarm"], (0.85, 0.20, 0.20, 1))


if __name__ == "__main__":
    unittest.main()
