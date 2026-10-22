"""Run a named NightWise scenario from the terminal."""

import argparse

from scenarios import get_scenario, get_scenarios
from simulation import Simulation


def run_scenario(name):
    """Return the simulation and its replay frames."""
    scenario = get_scenario(name)
    simulation = Simulation(agents=scenario.agents)

    frames = []

    # 120 frames represent intervals [0, 1), ... [119, 120).
    for time_s in range(scenario.duration_s):
        frame = simulation.step(
            time_s=time_s,
            **scenario.conditions_at(time_s),
        )

        frame["scenario"] = scenario.name
        frame["dt_s"] = 1.0
        frames.append(frame)

    return simulation, frames


def main():
    parser = argparse.ArgumentParser(
        description="Run a simulated NightWise scenario."
    )
    parser.add_argument(
        "--scenario",
        choices=list(get_scenarios()),
        default="one_pedestrian",
    )
    args = parser.parse_args()

    scenario = get_scenario(args.scenario)
    _, frames = run_scenario(args.scenario)

    print(f"Scenario: {scenario.name}")
    print(scenario.description)
    print(f"Duration: {scenario.duration_s}s")
    print(f"Frames: {len(frames)}")
    print("All readings and physical estimates are simulated.")

    print("\nLAMP STATE CHANGES")

    previous_states = {}

    for frame in frames:
        for lamp in frame["lamps"]:
            state = (
                lamp["brightness_pct"],
                lamp["mode"],
                lamp["sensor_status"],
            )

            if previous_states.get(lamp["lamp_id"]) != state:
                print(
                    f"{frame['time_s']:>3}s | "
                    f"{lamp['lamp_id']} | "
                    f"{lamp['brightness_pct']:>5.1f}% | "
                    f"{lamp['mode']:<9} | "
                    f"{lamp['sensor_status']}"
                )

            previous_states[lamp["lamp_id"]] = state


if __name__ == "__main__":
    main()