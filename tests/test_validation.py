import unittest
from copy import deepcopy

from nightwise.comparison import run_comparison
from nightwise.impact import compare_energy
from nightwise.runner import run_scenario
from nightwise.scenarios import get_scenario, get_scenarios
from nightwise.validation import validate_run


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.name = "one_pedestrian"
        simulation, self.frames = run_scenario(self.name)
        self.environment = simulation.environment
        self.end_s = float(get_scenario(self.name).duration_s)

    def validate(self, frames):
        validate_run(
            frames,
            self.environment,
            expected_start_s=0.0,
            expected_end_s=self.end_s,
        )

    def assert_rejected(self, mutate):
        frames = deepcopy(self.frames)
        mutate(frames)

        with self.assertRaises(ValueError):
            self.validate(frames)

    def test_all_named_scenarios_are_valid(self):
        for name in get_scenarios():
            with self.subTest(scenario=name):
                run_comparison(name)

    def test_duplicate_timestamp(self):
        self.assert_rejected(
            lambda frames: frames.insert(1, deepcopy(frames[0]))
        )

    def test_missing_middle_interval(self):
        self.assert_rejected(lambda frames: frames.pop(1))

    def test_missing_first_interval(self):
        self.assert_rejected(lambda frames: frames.pop(0))

    def test_missing_final_interval(self):
        self.assert_rejected(lambda frames: frames.pop())

    def test_empty_run(self):
        with self.assertRaises(ValueError):
            self.validate([])

    def test_invalid_durations(self):
        for value in (
            0, -1, float("nan"), float("inf"), True, "1", None
        ):
            with self.subTest(duration=value):
                self.assert_rejected(
                    lambda frames, value=value:
                    frames[0].update(dt_s=value)
                )

    def test_invalid_numeric_readings(self):
        for value in (float("nan"), float("inf"), -1):
            with self.subTest(field="total_power_w", value=value):
                self.assert_rejected(
                    lambda frames, value=value:
                    frames[0].update(total_power_w=value)
                )

            with self.subTest(field="lamp_power", value=value):
                self.assert_rejected(
                    lambda frames, value=value:
                    frames[0]["lamps"][0].update(power_w=value)
                )

            with self.subTest(field="lux", value=value):
                self.assert_rejected(
                    lambda frames, value=value:
                    frames[0]["lux_readings"][0].update(
                        artificial_lux=value
                    )
                )

    def test_missing_lamp_in_every_frame(self):
        def remove_lamp(frames):
            for frame in frames:
                frame["lamps"].pop()
                frame["total_power_w"] = sum(
                    lamp["power_w"] for lamp in frame["lamps"]
                )

        self.assert_rejected(remove_lamp)

    def test_missing_point_in_every_frame(self):
        def remove_point(frames):
            for frame in frames:
                frame["lux_readings"].pop()

        self.assert_rejected(remove_point)

    def test_duplicate_records(self):
        for key in ("lamps", "lux_readings"):
            with self.subTest(records=key):
                self.assert_rejected(
                    lambda frames, key=key:
                    frames[0][key].append(
                        deepcopy(frames[0][key][0])
                    )
                )

    def test_inconsistent_total_power(self):
        self.assert_rejected(
            lambda frames: frames[0].update(
                total_power_w=frames[0]["total_power_w"] + 1
            )
        )

    def test_same_gap_in_both_policies_is_rejected(self):
        adaptive = deepcopy(self.frames)
        baseline = deepcopy(self.frames)
        adaptive.pop(1)
        baseline.pop(1)

        with self.assertRaises(ValueError):
            compare_energy(adaptive, baseline)


if __name__ == "__main__":
    unittest.main()