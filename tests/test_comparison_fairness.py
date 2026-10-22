import unittest
from copy import deepcopy

from nightwise.comparison import run_comparison
from nightwise.impact import compare_energy, total_energy_kwh
from nightwise.scenarios import get_scenarios


class ComparisonFairnessTests(unittest.TestCase):
    def setUp(self):
        comparison = run_comparison("one_pedestrian")
        self.adaptive = comparison["nightwise"]
        self.baseline = comparison["fixed_baseline"]

    def assert_rejected(self, mutate):
        baseline = deepcopy(self.baseline)
        mutate(baseline)

        with self.assertRaises(ValueError):
            compare_energy(self.adaptive, baseline)

    def test_all_named_scenarios_pass(self):
        for name in get_scenarios():
            with self.subTest(scenario=name):
                comparison = run_comparison(name)
                adaptive = comparison["nightwise"]
                baseline = comparison["fixed_baseline"]

                result = compare_energy(adaptive, baseline)

                self.assertAlmostEqual(
                    result["adaptive_kwh"],
                    total_energy_kwh(adaptive),
                )
                self.assertAlmostEqual(
                    result["baseline_kwh"],
                    total_energy_kwh(baseline),
                )

    def test_missing_context_is_rejected(self):
        self.assert_rejected(
            lambda frames: frames[0].pop("comparison_context")
        )

    def test_fixture_specification_mismatch_is_rejected(self):
        def mutate(frames):
            frames[0]["comparison_context"]["environment"]["lamps"][0][
                "rated_power_w"
            ] += 1

        self.assert_rejected(mutate)

    def test_controller_configuration_mismatch_is_rejected(self):
        def mutate(frames):
            frames[0]["comparison_context"]["controller"][
                "hold_seconds"
            ] += 1

        self.assert_rejected(mutate)

    def test_measurement_geometry_mismatch_is_rejected(self):
        def mutate(frames):
            frames[0]["lux_readings"][0]["x_m"] += 1

        self.assert_rejected(mutate)

    def test_fixture_zone_mismatch_is_rejected(self):
        def mutate(frames):
            frames[0]["lamps"][0]["zone"] = "habitat_corridor"

        self.assert_rejected(mutate)

    def test_sensor_input_mismatch_is_rejected(self):
        def mutate(frames):
            lamp = frames[0]["lamps"][0]
            lamp["motion"] = not lamp["motion"]

        self.assert_rejected(mutate)

    def test_agent_input_mismatch_is_rejected(self):
        def mutate(frames):
            frame = next(frame for frame in frames if frame["agents"])
            frame["agents"] = []

        self.assert_rejected(mutate)

    def test_duration_mismatch_is_rejected(self):
        def mutate(frames):
            frames[-1]["dt_s"] += 1

        self.assert_rejected(mutate)

    def test_incorrect_baseline_policy_is_rejected(self):
        def mutate(frames):
            frame = frames[0]
            lamp = frame["lamps"][0]
            lamp["brightness_pct"] = 0
            lamp["power_w"] = 0
            frame["total_power_w"] = sum(
                item["power_w"] for item in frame["lamps"]
            )

        self.assert_rejected(mutate)

    def test_missing_fixture_is_rejected(self):
        self.assert_rejected(
            lambda frames: frames[0]["lamps"].pop()
        )

    def test_missing_measurement_point_is_rejected(self):
        self.assert_rejected(
            lambda frames: frames[0]["lux_readings"].pop()
        )

    def test_same_gap_in_both_runs_is_rejected(self):
        adaptive = deepcopy(self.adaptive)
        baseline = deepcopy(self.baseline)
        adaptive.pop(1)
        baseline.pop(1)

        with self.assertRaises(ValueError):
            compare_energy(adaptive, baseline)

    def test_empty_runs_are_rejected(self):
        with self.assertRaises(ValueError):
            compare_energy([], [])


if __name__ == "__main__":
    unittest.main()