"""Export matched NightWise simulations for dashboard and impact work."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

from comparison import run_comparison
from scenarios import get_scenario, get_scenarios


def write_csv(path, rows):
    """Write nonempty rows with a consistent field order."""
    if not rows:
        return

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)


def export_scenario(scenario_name, output_root):
    scenario = get_scenario(scenario_name)
    comparison = run_comparison(scenario_name)

    output_dir = Path(output_root) / scenario_name
    output_dir.mkdir(parents=True, exist_ok=True)

    sensor_rows = []
    agent_rows = []
    lamp_rows = []
    lux_rows = []

    # Sensor inputs and agents are shared between both policies.
    for frame in comparison["nightwise"]:
        common = {
            "scenario": scenario_name,
            "data_source": "simulated",
            "time_s": frame["time_s"],
            "dt_s": frame["dt_s"],
        }

        for lamp in frame["lamps"]:
            sensor_rows.append({
                **common,
                "lamp_id": lamp["lamp_id"],
                "zone": lamp["zone"],
                "motion": lamp["motion"],
                "is_night": lamp["is_night"],
                "sensor_ok": lamp["sensor_ok"],
                "sensor_status": lamp["sensor_status"],
                "sample_age_s": lamp["sample_age_s"],
            })

        for agent in frame["agents"]:
            agent_rows.append({
                **common,
                **agent,
                "active": True,
            })

    # Export physical outputs separately for each policy.
    for policy in ("fixed_baseline", "nightwise"):
        for frame in comparison[policy]:
            common = {
                "scenario": scenario_name,
                "data_source": "simulated",
                "policy": policy,
                "time_s": frame["time_s"],
                "dt_s": frame["dt_s"],
            }

            for lamp in frame["lamps"]:
                lamp_rows.append({
                    **common,
                    "lamp_id": lamp["lamp_id"],
                    "zone": lamp["zone"],
                    "brightness_pct": lamp["brightness_pct"],
                    "mode": lamp["mode"],
                    "reason": lamp["reason"],
                    "power_w": lamp["power_w"],
                    "interval_energy_kwh": (
                        lamp["power_w"]
                        * frame["dt_s"]
                        / 3_600_000
                    ),
                })

            for point in frame["lux_readings"]:
                lux_rows.append({
                    **common,
                    **point,
                    "interval_exposure_lux_s": (
                        point["artificial_lux"] * frame["dt_s"]
                    ),
                })

    write_csv(output_dir / "sensor_inputs.csv", sensor_rows)
    write_csv(output_dir / "lamp_outputs.csv", lamp_rows)
    write_csv(output_dir / "lux_readings.csv", lux_rows)

    # Always create this CSV, including for scenarios with no agents.
    agent_path = output_dir / "agent_positions.csv"

    with agent_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "scenario",
                "data_source",
                "time_s",
                "dt_s",
                "agent_id",
                "agent_type",
                "x_m",
                "y_m",
                "active",
            ],
        )
        writer.writeheader()
        writer.writerows(agent_rows)

    controller_config_path = Path(__file__).with_name(
        "controller_config.json"
    )

    with controller_config_path.open(encoding="utf-8") as file:
        controller_config = json.load(file)

    metadata = {
        "model_version": "nightwise-simulation-v1",
        "data_source": "simulated",
        "scenario": asdict(scenario),
        "environment": comparison["environment"],
        "controller_config": controller_config,
        "time_step_s": 1.0,
        "interval_convention": (
            "Each frame applies over [time_s, time_s + dt_s)."
        ),
        "baseline": {
            "nighttime": "Fixed brightness at each zone's cap.",
            "daytime": "Off according to scenario schedule.",
            "sensor_dependency": (
                "None; sensor inputs are shared for comparison only."
            ),
            "fixture_and_shielding": "Identical to NightWise.",
        },
        "assumptions": {
            "power": (
                "power_w = rated_power_w * brightness_pct / 100"
            ),
            "lux": (
                "Sum over lamps: full_output_lux_below * "
                "(brightness_pct / 100) * "
                "height_m^2 / (height_m^2 + horizontal_distance_m^2) "
                "* directional_factor"
            ),
            "directional_factor": (
                "habitat_spill_factor for habitat_edge and "
                "habitat_corridor points; otherwise 1."
            ),
            "sensor_geometry": (
                "Ideal circular detection range; active agents "
                "move continuously. Agent type is not used."
            ),
            "stale_rule": (
                "Unhealthy when no sample exists or sample age "
                "exceeds sensor_stale_timeout_s."
            ),
            "agent_logging": (
                "Only active agents have position rows. "
                "An absent row means the agent is outside the environment."
            ),
            "exclusions": [
                "Standby, sensor and communication power",
                "Ambient daylight and other light sources",
                "Calibrated fixture photometry",
                "Spectrum and species-specific effects",
            ],
        },
        "limitations": [
            "Illustrative estimates, not field measurements.",
            "Energy results apply only to the simulated duration.",
            "Lower habitat lux does not demonstrate wildlife recovery.",
            "Visibility and safety compliance have not been validated.",
            "NightWise sensor-fault fallback takes priority over daytime.",
        ],
        "row_counts": {
            "sensor_inputs": len(sensor_rows),
            "agent_positions": len(agent_rows),
            "lamp_outputs": len(lamp_rows),
            "lux_readings": len(lux_rows),
        },
    }

    with (output_dir / "run_metadata.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(metadata, file, indent=2, allow_nan=False)

    print(f"\nExported: {scenario_name}")
    print(f"Folder: {output_dir.resolve()}")

    for name, count in metadata["row_counts"].items():
        print(f"  {name}: {count} rows")


def main():
    parser = argparse.ArgumentParser(
        description="Export matched simulation logs."
    )
    parser.add_argument(
        "--scenario",
        choices=["all", *get_scenarios()],
        default="all",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).with_name("outputs"),
    )
    args = parser.parse_args()

    names = (
        list(get_scenarios())
        if args.scenario == "all"
        else [args.scenario]
    )

    for name in names:
        export_scenario(name, args.output_dir)


if __name__ == "__main__":
    main()