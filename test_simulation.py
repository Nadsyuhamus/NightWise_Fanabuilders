"""Integration and calculation checks for Person 2's simulation."""

import unittest

from agents import Agent
from comparison import run_comparison, total_energy_kwh
from environment import load_environment
from models import (
    estimate_power_w,
    estimate_lamp_lux,
    estimate_point_lux,
)
from scenarios import get_scenarios
from sensors import detects_motion
from simulation import Simulation


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.environment = load_environment()

    def test_agent_entry_position_and_departure(self):
        agent = Agent(
            agent_id="TEST_PERSON",
            agent_type="person",
            route=((0.0, 10.0), (60.0, 10.0)),
            speed_m_s=1.2,
            start_time_s=5.0,
        )

        self.assertIsNone(agent.position_at(4))
        self.assertEqual(agent.position_at(5), (0.0, 10.0))
        self.assertEqual(agent.position_at(30), (30.0, 10.0))
        self.assertIsNone(agent.position_at(55))

    def test_sensor_range_and_agent_type_independence(self):
        lamp = self.environment["lamps"][0]

        for agent_type in ("person", "animal"):
            agent = Agent(
                agent_id="TEST_AGENT",
                agent_type=agent_type,
                route=((0.0, 10.0), (60.0, 10.0)),
                speed_m_s=1.0,
            )

            # P1 is at (10, 10), with an 8 m detection radius.
            self.assertFalse(detects_motion(lamp, [agent], 1))
            self.assertTrue(detects_motion(lamp, [agent], 2))
            self.assertTrue(detects_motion(lamp, [agent], 18))
            self.assertFalse(detects_motion(lamp, [agent], 19))

    def test_power_and_energy_units(self):
        self.assertEqual(estimate_power_w(40, 0), 0)
        self.assertEqual(estimate_power_w(40, 70), 28)

        one_hour = [{
            "total_power_w": 40,
            "dt_s": 3600,
        }]

        self.assertAlmostEqual(
            total_energy_kwh(one_hour),
            0.04,
        )

        for invalid_brightness in (-1, 101, float("nan")):
            with self.assertRaises(ValueError):
                estimate_power_w(40, invalid_brightness)

    def test_lux_zero_and_multiple_lamp_contributions(self):
        lamps = self.environment["lamps"]
        point = self.environment["measurement_points"][-2]

        zero_brightness = {
            lamp["lamp_id"]: 0.0 for lamp in lamps
        }

        self.assertEqual(
            estimate_point_lux(lamps, zero_brightness, point),
            0.0,
        )

        brightness = {
            lamp["lamp_id"]: 30.0 for lamp in lamps
        }

        individual_contributions = [
            estimate_lamp_lux(lamp, 30.0, point)
            for lamp in lamps
        ]

        self.assertAlmostEqual(
            estimate_point_lux(lamps, brightness, point),
            sum(individual_contributions),
        )
        self.assertGreater(sum(individual_contributions), 0)

    def test_independent_lamps_and_daylight(self):
        agent = Agent(
            agent_id="TEST_PERSON",
            agent_type="person",
            route=((0.0, 10.0), (60.0, 10.0)),
            speed_m_s=1.2,
            start_time_s=5.0,
        )
        simulation = Simulation([agent])

        for time_s in range(11):
            frame = simulation.step(time_s)

        lamps = {
            lamp["lamp_id"]: lamp for lamp in frame["lamps"]
        }

        self.assertEqual(lamps["P1"]["brightness_pct"], 70)
        self.assertEqual(lamps["P2"]["brightness_pct"], 30)
        self.assertEqual(lamps["E1"]["brightness_pct"], 10)

        daytime = simulation.step(11, is_night=False)

        self.assertEqual(daytime["total_power_w"], 0)
        self.assertTrue(all(
            point["artificial_lux"] == 0
            for point in daytime["lux_readings"]
        ))

    def test_explicit_fault_and_recovery(self):
        simulation = Simulation([])

        frame = simulation.step(0, faulty_lamp_ids={"P1"})
        p1 = next(
            lamp for lamp in frame["lamps"]
            if lamp["lamp_id"] == "P1"
        )

        self.assertEqual(p1["sensor_status"], "fault")
        self.assertEqual(p1["brightness_pct"], 50)

        recovered = simulation.step(1)
        p1 = next(
            lamp for lamp in recovered["lamps"]
            if lamp["lamp_id"] == "P1"
        )

        self.assertEqual(p1["sensor_status"], "healthy")
        self.assertEqual(p1["brightness_pct"], 40)

    def test_missing_stale_and_recovered_samples(self):
        simulation = Simulation([])

        missing_frame = simulation.step(0, stale_lamp_ids={"P1"})
        p1 = next(
            lamp for lamp in missing_frame["lamps"]
            if lamp["lamp_id"] == "P1"
        )

        self.assertEqual(p1["sensor_status"], "missing")
        self.assertIsNone(p1["sample_age_s"])
        self.assertEqual(p1["mode"], "fallback")

        simulation.reset()

        for time_s in range(12):
            blocked = {"P1"} if 4 <= time_s < 10 else set()
            frame = simulation.step(
                time_s,
                stale_lamp_ids=blocked,
            )
            p1 = next(
                lamp for lamp in frame["lamps"]
                if lamp["lamp_id"] == "P1"
            )

            if time_s == 6:
                self.assertEqual(p1["sample_age_s"], 3)
                self.assertEqual(p1["sensor_status"], "healthy")
            elif time_s == 7:
                self.assertEqual(p1["sensor_status"], "stale")
                self.assertEqual(p1["brightness_pct"], 50)
            elif time_s == 10:
                self.assertEqual(p1["sensor_status"], "healthy")
                self.assertEqual(p1["brightness_pct"], 40)
            elif time_s == 11:
                self.assertEqual(p1["brightness_pct"], 30)

    def test_reset_replays_identically(self):
        scenario = get_scenarios()["one_pedestrian"]
        simulation = Simulation(scenario.agents)

        def replay():
            return [
                simulation.step(t, **scenario.conditions_at(t))
                for t in range(scenario.duration_s)
            ]

        first_run = replay()
        simulation.reset()
        second_run = replay()

        self.assertEqual(first_run, second_run)

    def test_all_scenarios_have_matched_inputs_and_duration(self):
        input_fields = (
            "lamp_id",
            "zone",
            "time_s",
            "motion",
            "is_night",
            "sensor_ok",
            "sensor_status",
            "sample_age_s",
        )

        for name, scenario in get_scenarios().items():
            with self.subTest(scenario=name):
                result = run_comparison(name)
                baseline = result["fixed_baseline"]
                adaptive = result["nightwise"]

                self.assertEqual(len(baseline), scenario.duration_s)
                self.assertEqual(len(adaptive), scenario.duration_s)
                self.assertEqual(
                    sum(frame["dt_s"] for frame in adaptive),
                    scenario.duration_s,
                )

                for fixed_frame, adaptive_frame in zip(
                    baseline, adaptive
                ):
                    self.assertEqual(
                        fixed_frame["time_s"],
                        adaptive_frame["time_s"],
                    )
                    self.assertEqual(
                        fixed_frame["agents"],
                        adaptive_frame["agents"],
                    )

                    for fixed_lamp, adaptive_lamp in zip(
                        fixed_frame["lamps"],
                        adaptive_frame["lamps"],
                    ):
                        for field in input_fields:
                            self.assertEqual(
                                fixed_lamp[field],
                                adaptive_lamp[field],
                            )

                        expected_baseline = (
                            70.0
                            if fixed_lamp["zone"] == "walking_path"
                            else 30.0
                        )
                        if not fixed_lamp["is_night"]:
                            expected_baseline = 0.0

                        self.assertEqual(
                            fixed_lamp["brightness_pct"],
                            expected_baseline,
                        )


if __name__ == "__main__":
    unittest.main()