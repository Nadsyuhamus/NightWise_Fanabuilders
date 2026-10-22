"""Matched fixed-lighting and NightWise scenario comparisons."""

from nightwise.impact import (
    build_baseline_frame,
    compare_energy,
    total_energy_kwh,
)
from nightwise.runner import run_scenario
from nightwise.scenarios import get_scenario
from nightwise.validation import validate_run


def run_comparison(scenario_name):
    """Return complete, validated adaptive and fixed runs."""
    scenario = get_scenario(scenario_name)
    simulation, adaptive_frames = run_scenario(scenario_name)

    validation_options = {
        "expected_start_s": 0.0,
        "expected_end_s": float(scenario.duration_s),
    }

    # Validate before deriving the baseline. Otherwise incomplete
    # adaptive data could be copied into both policies.
    validate_run(
        adaptive_frames,
        simulation.environment,
        **validation_options,
    )

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

    validate_run(
        baseline_frames,
        simulation.environment,
        **validation_options,
    )

    return {
        "environment": simulation.environment,
        "nightwise": adaptive_frames,
        "fixed_baseline": baseline_frames,
    }


def main():
    comparison = run_comparison("one_pedestrian")

    impact = compare_energy(
        comparison["nightwise"],
        comparison["fixed_baseline"],
    )

    duration_s = sum(
        frame["dt_s"] for frame in comparison["nightwise"]
    )

    print("SIMULATED MATCHED COMPARISON")
    print("Scenario: one_pedestrian")
    print(f"Duration: {duration_s:g} seconds")
    print("Baseline: fixed nighttime brightness at each zone's cap")
    print("Same fixtures, shielding, agents and sensor inputs")
    print()
    print(f"Baseline energy:  {impact['baseline_kwh']:.6f} kWh")
    print(f"NightWise energy: {impact['adaptive_kwh']:.6f} kWh")
    print(f"Energy difference: {impact['saved_kwh']:.6f} kWh")

    if impact["savings_pct"] is None:
        print("Energy reduction percentage: undefined (zero baseline)")
    else:
        print(
            f"Estimated energy reduction: "
            f"{impact['savings_pct']:.2f}%"
        )


if __name__ == "__main__":
    main()