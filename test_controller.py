import unittest
from controller import LightingController, SensorInput


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.c = LightingController()

    def update(self, t, motion=False, zone="walking_path", lamp="L1", **flags):
        return self.c.update(SensorInput(lamp, zone, t, motion, flags.get("is_night", True), flags.get("sensor_ok", True)))

    def test_hold_then_partial_interval_fade(self):
        self.assertEqual(self.update(0, True).brightness_pct, 70)
        self.assertEqual(self.update(29).brightness_pct, 70)
        self.assertEqual(self.update(32).brightness_pct, 50)
        self.assertEqual(self.update(35).brightness_pct, 30)

    def test_new_motion_extends_hold(self):
        self.update(0, True)
        self.update(20, True)
        self.assertEqual(self.update(49).brightness_pct, 70)

    def test_fault_daylight_and_recovery(self):
        self.update(0, True)
        self.assertEqual(self.update(1, sensor_ok=False).brightness_pct, 50)
        self.assertEqual(self.update(2, True).brightness_pct, 70)
        self.assertEqual(self.update(3, is_night=False).brightness_pct, 0)

    def test_zone_limits_and_independent_lamps(self):
        self.assertEqual(self.update(0, True, "habitat_edge", "E1").brightness_pct, 30)
        self.assertEqual(self.update(0, True, "habitat_corridor", "H1").brightness_pct, 0)
        self.assertEqual(self.update(0).brightness_pct, 30)

    def test_invalid_time_and_reset(self):
        self.update(5)
        with self.assertRaises(ValueError):
            self.update(4)
        self.c.reset()
        self.assertEqual(self.update(0).brightness_pct, 30)


if __name__ == "__main__":
    unittest.main()

