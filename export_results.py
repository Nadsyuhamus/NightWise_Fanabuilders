"""Export matched NightWise simulations for dashboard and impact work."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

from comparison import run_comparison
from scenarios import get_scenario, get_scenarios
from impact import (
    compare_energy,
    format_reduction_pct,
    habitat_summary,
    path_visibility_summary,
)

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

    visibility_rows = []

    for policy in ("fixed_baseline", "nightwise"):
        summary = path_visibility_summary(
            comparison[policy],
            comparison["environment"],
        )

        visibility_rows.append({
            "scenario": scenario_name,
            "data_source": "simulated",
            "policy": policy,
            **summary,
        })

    write_csv(
        output_dir / "path_visibility_summary.csv",
        visibility_rows,
    )

    energy_summary = compare_energy(
    comparison["nightwise"],
    comparison["fixed_baseline"],
    )

    write_csv(
        output_dir / "impact_summary.csv",
        [{
            "scenario": scenario_name,
            "data_source": "simulated",
            "baseline_policy": "fixed_zone_cap",
            "duration_s": sum(
                frame["dt_s"] for frame in comparison["nightwise"]
            ),
            **energy_summary,
            "savings_pct_display": format_reduction_pct(
                energy_summary["savings_pct"]
            ),
            "savings_pct_status": (
                "undefined_zero_baseline"
                if energy_summary["savings_pct"] is None
                else "defined"
            ),
            "energy_difference_definition": "baseline_kwh - adaptive_kwh",
        }],
    )

    habitat_rows = []
    habitat_point_rows = []

    points_by_id = {
        point["point_id"]: point
        for point in comparison["environment"]["measurement_points"]
    }
    for zone in ("habitat_edge", "habitat_corridor"):
        point_ids = [
            point["point_id"]
            for point in comparison["environment"]["measurement_points"]
            if point["zone"] == zone
        ]

        if not point_ids:
            continue

        for policy in ("fixed_baseline", "nightwise"):
            for night_only in (True, False):
                summary = habitat_summary(
                    comparison[policy],
                    point_ids,
                    night_only=night_only,
                )

                habitat_rows.append({
                    "scenario": scenario_name,
                    "data_source": "simulated",
                    "policy": policy,
                    "zone": zone,
                    "measurement_point_ids": "|".join(point_ids),
                    **{
                        key: value
                        for key, value in summary.items()
                        if key != "points"
                    },
                })

                for point_summary in summary["points"]:
                    point = points_by_id[point_summary["point_id"]]

                    habitat_point_rows.append({
                        "scenario": scenario_name,
                        "data_source": "simulated",
                        "policy": policy,
                        "zone": zone,
                        "scope": summary["scope"],
                        "duration_s": summary["duration_s"],
                        "x_m": point["x_m"],
                        "y_m": point["y_m"],
                        **point_summary,
                    })

    write_csv(
        output_dir / "habitat_summary.csv",
        habitat_rows,
    )
    write_csv(
        output_dir / "habitat_point_summary.csv",
        habitat_point_rows,
    )

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
                "daylight_ok": lamp["daylight_ok"],
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
            "habitat_summary": (
                "Mean lux is weighted by interval duration. "
                "Exposure_lux_s = sum(artificial_lux * dt_s). "
                "Exposure_lux_h = exposure_lux_s / 3600. "
                "Peak lux is the maximum eligible interval reading. "
                "Zone means use equal weights per configured point; "
                "they are not area-weighted habitat estimates. "
                "Edge and corridor are summarised separately."
            ),
            "power": (
                "power_w = rated_power_w * brightness_pct / 100. "
                "Power is assumed proportional to brightness. "
                "This assumption has not been checked against real lamps. "
                "Standby, sensor, controller and communication power are excluded."
            ),
            "lux": (
                "Sum over lamps: full_output_lux_below * "
                "(brightness_pct / 100) * "
                "height_m^2 / (height_m^2 + horizontal_distance_m^2) "
                "* directional_factor"
            ),
            "directional_factor": (
                "For habitat measurement points, each lamp's calculated light "
                "is multiplied by its configured habitat_spill_factor. "
                "This also applies to the habitat-edge lamp. "
                "For other measurement points, the multiplier is 1. "
                "This is a simplified assumption based on the point's zone, "
                "not a measured physical shield or beam direction. "
                "Both fixed and adaptive lighting use the same multipliers."
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
            "sensor_ok describes motion input health only.",
            "daylight_ok describes availability of the shared day/night input.",
            "Reliable daytime keeps lamps off despite motion faults.",
            "Unavailable day/night input activates configured zone fallback.",
            "The fixed baseline retains an independent scenario schedule; "
            "daylight-input-fault runs compare different input availability.",
        ],
        "row_counts": {
            "sensor_inputs": len(sensor_rows),
            "agent_positions": len(agent_rows),
            "lamp_outputs": len(lamp_rows),
            "lux_readings": len(lux_rows),
            "habitat_summary": len(habitat_rows),
            "habitat_point_summary": len(habitat_point_rows),
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