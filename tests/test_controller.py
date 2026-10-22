import json
from pathlib import Path
import tempfile
import unittest

from controller import LightingController, SensorInput


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.c = LightingController()

    def send(
        self,
        t,
        motion=False,
        zone="walking_path",
        lamp="L1",
        night=True,
        healthy=True,
    ):
        return self.c.update(
            SensorInput(
                lamp,
                zone,
                t,
                motion,
                night,
                healthy,
            )
        )

    def test_empty(self):
        self.assertEqual(
            self.send(0).brightness_pct,
            30,
        )
        self.assertEqual(
            self.send(10).mode,
            "idle",
        )

    def test_hold_and_fade(self):
        self.send(0, True)

        self.assertEqual(
            self.send(30).brightness_pct,
            70,
        )
        self.assertEqual(
            self.send(31).brightness_pct,
            60,
        )
        self.assertEqual(
            self.send(34).brightness_pct,
            30,
        )

    def test_irregular_interval(self):
        self.send(0, True)
        self.send(29)

        self.assertEqual(
            self.send(32).brightness_pct,
            50,
        )

    def test_repeated_motion(self):
        self.send(0, True)
        self.send(20, True)

        self.assertEqual(
            self.send(49).brightness_pct,
            70,
        )
        self.assertEqual(
            self.send(51).brightness_pct,
            60,
        )

    def test_fault_and_recovery(self):
        self.send(0, True)

        self.assertEqual(
            self.send(1, healthy=False).brightness_pct,
            50,
        )
        self.assertEqual(
            self.send(2).brightness_pct,
            40,
        )
        self.assertEqual(
            self.send(3).brightness_pct,
            30,
        )
        self.assertEqual(
            self.send(4, True).brightness_pct,
            70,
        )

    def test_day_to_night(self):
        self.assertEqual(
            self.send(0, night=False).brightness_pct,
            0,
        )
        self.assertEqual(
            self.send(1).brightness_pct,
            30,
        )
        self.assertEqual(
            self.send(2, True).brightness_pct,
            70,
        )

    def test_daytime_overrides_motion_fault(self):
        for zone in self.c.profiles:
            with self.subTest(zone=zone):
                result = self.send(
                    0,
                    motion=True,
                    zone=zone,
                    lamp=zone,
                    night=False,
                    healthy=False,
                )
                self.assertEqual(result.mode, "daylight")
                self.assertEqual(result.brightness_pct, 0)
                self.assertIn("unhealthy", result.reason)

    def test_fault_persists_into_night(self):
        self.send(0, night=False, healthy=False)

        result = self.send(1, healthy=False)

        self.assertEqual(result.mode, "fallback")
        self.assertEqual(result.brightness_pct, 50)

    def test_daytime_clears_motion_history(self):
        self.send(0, motion=True)
        self.send(1, night=False, healthy=False)

        result = self.send(2)

        self.assertEqual(result.mode, "idle")
        self.assertEqual(result.brightness_pct, 30)

    def test_edge_and_corridor(self):
        self.assertEqual(
            self.send(
                0, True, "habitat_edge", "E"
            ).brightness_pct,
            30,
        )

        self.assertEqual(
            self.send(
                1,
                zone="habitat_edge",
                lamp="E",
                healthy=False,
            ).brightness_pct,
            20,
        )

        self.assertEqual(
            self.send(
                0, True, "habitat_corridor", "H"
            ).brightness_pct,
            0,
        )

        self.assertEqual(
            self.send(
                1,
                zone="habitat_corridor",
                lamp="H",
                healthy=False,
            ).brightness_pct,
            0,
        )

    def test_independent_lamps(self):
        self.send(0, True, lamp="A")

        self.assertEqual(
            self.send(0, lamp="B").brightness_pct,
            30,
        )
        self.assertEqual(
            self.send(1, lamp="A").brightness_pct,
            70,
        )

    def test_time_and_reset(self):
        self.send(5)

        for t in (5, 4):
            with self.assertRaises(ValueError):
                self.send(t)

        self.c.reset()
        self.assertEqual(self.send(0).mode, "idle")

    def test_invalid_inputs(self):
        readings = [
            SensorInput(
                "", "walking_path", 0, False, True
            ),
            SensorInput(
                "L", "unknown", 0, False, True
            ),
            SensorInput(
                "L", "walking_path",
                float("nan"), False, True
            ),
            SensorInput(
                "L", "walking_path", -1, False, True
            ),
            SensorInput(
                "L", "walking_path", 0, 1, True
            ),
        ]

        for reading in readings:
            with self.assertRaises(ValueError):
                self.c.update(reading)

    def test_zone_change(self):
        self.send(0)

        with self.assertRaises(ValueError):
            self.send(1, zone="habitat_edge")

    def test_config_validation_and_custom_hold(self):
        config_path = Path(__file__).with_name(
            "controller_config.json"
        )
        config = json.loads(config_path.read_text())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"

            config["hold_seconds"] = 5
            path.write_text(json.dumps(config))

            self.c = LightingController(path)
            self.send(0, True)

            self.assertEqual(
                self.send(6).brightness_pct,
                60,
            )

            # Invalid fallback exceeds habitat-edge cap.
            config["zones"]["habitat_edge"]["fallback"] = 99
            path.write_text(json.dumps(config))

            with self.assertRaises(ValueError):
                LightingController(path)


if __name__ == "__main__":
    unittest.main()