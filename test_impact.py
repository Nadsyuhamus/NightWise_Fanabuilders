import unittest

from impact import (
    compare_energy,
    format_reduction_pct,
    habitat_summary,
)


def energy_frame(power_w):
    return {
        "time_s": 0,
        "dt_s": 3600,
        "total_power_w": power_w,
    }


def lux_frame(time_s, dt_s, is_night, lux):
    return {
        "time_s": time_s,
        "dt_s": dt_s,
        "lamps": [{"is_night": is_night}],
        "lux_readings": [
            {"point_id": "H1", "artificial_lux": lux}
        ],
    }


class ImpactTests(unittest.TestCase):
    def test_zero_baseline_with_no_consumption(self):
        result = compare_energy(
            [energy_frame(0)],
            [energy_frame(0)],
        )
        self.assertIsNone(result["savings_pct"])
        self.assertEqual(result["saved_kwh"], 0)
        self.assertEqual(
            format_reduction_pct(result["savings_pct"]),
            "N/A",
        )

    def test_zero_baseline_with_extra_consumption(self):
        result = compare_energy(
            [energy_frame(1)],
            [energy_frame(0)],
        )
        self.assertIsNone(result["savings_pct"])
        self.assertAlmostEqual(result["saved_kwh"], -0.001)

    def test_negative_savings_are_preserved(self):
        result = compare_energy(
            [energy_frame(1.2)],
            [energy_frame(1)],
        )
        self.assertAlmostEqual(result["savings_pct"], -20)
        self.assertAlmostEqual(result["saved_kwh"], -0.0002)

    def test_scope_and_duration_weighting(self):
        frames = [
            lux_frame(0, 10, True, 2),
            lux_frame(10, 30, True, 6),
            lux_frame(40, 20, False, 0),
        ]

        night = habitat_summary(frames, ["H1"], night_only=True)
        full = habitat_summary(frames, ["H1"], night_only=False)

        self.assertEqual(night["duration_s"], 40)
        self.assertEqual(full["duration_s"], 60)
        self.assertAlmostEqual(night["mean_lux"], 5)
        self.assertAlmostEqual(full["mean_lux"], 200 / 60)

        # Daytime adds zero artificial lux, so exposure is unchanged.
        self.assertAlmostEqual(
            night["mean_point_exposure_lux_h"], 200 / 3600
        )
        self.assertAlmostEqual(
            full["mean_point_exposure_lux_h"], 200 / 3600
        )

    def test_no_night_readings_are_not_reported_as_zero(self):
        summary = habitat_summary(
            [lux_frame(0, 10, False, 0)],
            ["H1"],
            night_only=True,
        )
        self.assertEqual(summary["duration_s"], 0)
        self.assertIsNone(summary["mean_lux"])
        self.assertIsNone(summary["mean_point_exposure_lux_h"])

    def test_missing_readings_fail_instead_of_biasing_mean(self):
        with self.assertRaises(ValueError):
            habitat_summary(
                [lux_frame(0, 10, True, 2)],
                ["H1", "H2"],
            )

    def test_per_point_mean_peak_and_exposure(self):
        frames = [
            {
                "time_s": 0,
                "dt_s": 10,
                "lamps": [{"is_night": True}],
                "lux_readings": [
                    {"point_id": "H1", "artificial_lux": 2},
                    {"point_id": "H2", "artificial_lux": 8},
                ],
            },
            {
                "time_s": 10,
                "dt_s": 30,
                "lamps": [{"is_night": True}],
                "lux_readings": [
                    {"point_id": "H1", "artificial_lux": 6},
                    {"point_id": "H2", "artificial_lux": 0},
                ],
            },
        ]

        summary = habitat_summary(frames, ["H1", "H2"])
        points = {
            point["point_id"]: point
            for point in summary["points"]
        }

        # H1: (2*10 + 6*30) / 40 = 5 lux.
        self.assertAlmostEqual(points["H1"]["mean_lux"], 5)
        self.assertAlmostEqual(points["H1"]["peak_lux"], 6)
        self.assertAlmostEqual(points["H1"]["exposure_lux_s"], 200)
        self.assertAlmostEqual(
            points["H1"]["exposure_lux_h"], 200 / 3600
        )

        # H2: (8*10 + 0*30) / 40 = 2 lux.
        self.assertAlmostEqual(points["H2"]["mean_lux"], 2)
        self.assertAlmostEqual(points["H2"]["peak_lux"], 8)
        self.assertAlmostEqual(points["H2"]["exposure_lux_s"], 80)

        self.assertAlmostEqual(summary["mean_lux"], 3.5)
        self.assertAlmostEqual(summary["peak_lux"], 8)
        self.assertAlmostEqual(
            summary["mean_point_exposure_lux_s"], 140
        )

    def test_no_eligible_readings_have_no_peak_or_exposure(self):
        summary = habitat_summary(
            [lux_frame(0, 10, False, 4)],
            ["H1"],
            night_only=True,
        )

        self.assertIsNone(summary["peak_lux"])
        self.assertIsNone(summary["mean_point_exposure_lux_s"])
        self.assertIsNone(summary["points"][0]["peak_lux"])
        self.assertIsNone(summary["points"][0]["exposure_lux_s"])


if __name__ == "__main__":
    unittest.main()