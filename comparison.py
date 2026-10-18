"""Matched fixed-lighting and NightWise scenario comparisons."""

from copy import deepcopy

from models import estimate_power_w, estimate_point_lux
from run_simulation import run_scenario


def build_baseline_frame(adaptive_frame, environment, profiles):
    """Apply fixed nighttime brightness to the same scenario frame."""
    frame = deepcopy(adaptive_frame)
    frame["policy"] = "fixed_baseline"

    lamps_by_id = {
        lamp["lamp_id"]: lamp
        for lamp in environment["lamps"]
    }

    for result in frame["lamps"]:
        fixture = lamps_by_id[result["lamp_id"]]

        # Baseline follows the scenario's day/night schedule.
        # It does not use motion sensors to control brightness.
        brightness = (
            profiles[result["zone"]].cap
            if result["is_night"]
            else 0.0
        )

        result["brightness_pct"] = brightness
        result["mode"] = (
            "fixed_night" if result["is_night"] else "daylight"
        )
        result["reason"] = (
            "Fixed nighttime baseline; motion does not affect output"
            if result["is_night"]
            else "Scheduled daytime: lamp off"
        )
        result["power_w"] = estimate_power_w(
            fixture["rated_power_w"],
            brightness,
        )

    brightness_by_id = {
        lamp["lamp_id"]: lamp["brightness_pct"]
        for lamp in frame["lamps"]
    }

    frame["lux_readings"] = [
        {
            "point_id": point["point_id"],
            "zone": point["zone"],
            "x_m": point["x_m"],
            "y_m": point["y_m"],
            "artificial_lux": estimate_point_lux(
                environment["lamps"],
                brightness_by_id,
                point,
            ),
        }
        for point in environment["measurement_points"]
    ]

    frame["total_power_w"] = sum(
        lamp["power_w"] for lamp in frame["lamps"]
    )

    return frame


def run_comparison(scenario_name):
    """Return matched runs using one shared sequence of sensor inputs."""
    simulation, adaptive_frames = run_scenario(scenario_name)

    baseline_frames = []

    for frame in adaptive_frames:
        frame["policy"] = "nightwise"

        baseline_frames.append(
            build_baseline_frame(
                adaptive_frame=frame,
                environment=simulation.environment,
                profiles=simulation.controller.profiles,
            )
        )

    return {
        "environment": simulation.environment,
        "nightwise": adaptive_frames,
        "fixed_baseline": baseline_frames,
    }


def total_energy_kwh(frames):
    """Integrate power over the logged simulation intervals."""
    return sum(
        frame["total_power_w"] * frame["dt_s"] / 3_600_000
        for frame in frames
    )


def main():
    comparison = run_comparison("one_pedestrian")

    baseline_energy = total_energy_kwh(
        comparison["fixed_baseline"]
    )
    adaptive_energy = total_energy_kwh(
        comparison["nightwise"]
    )

    print("SIMULATED MATCHED COMPARISON")
    print("Scenario: one_pedestrian")
    print("Duration: 120 seconds")
    print("Baseline: fixed nighttime brightness at each zone's cap")
    print("Same fixtures, shielding, agents and sensor inputs")
    print()
    print(f"Baseline energy:  {baseline_energy:.6f} kWh")
    print(f"NightWise energy: {adaptive_energy:.6f} kWh")

    if baseline_energy > 0:
        savings_pct = (
            (baseline_energy - adaptive_energy)
            / baseline_energy
            * 100
        )
        print(f"Estimated energy reduction: {savings_pct:.2f}%")
    else:
        print("Energy reduction percentage: undefined (zero baseline)")


if __name__ == "__main__":
    main()