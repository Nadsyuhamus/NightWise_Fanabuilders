from nightwise.paths import LOG_DIR
"""Synthetic inputs for rule-based tests only; no AI training."""

from dataclasses import asdict
from pathlib import Path
import csv

from nightwise.controller import LightingController, SensorInput


# Each event: time_s, motion, is_night, sensor_ok.
SCENARIOS = {
    "empty": [
        (0, False, True, True),
        (10, False, True, True),
    ],
    "hold_and_fade": [
        (0, True, True, True),
        (30, False, True, True),
        (31, False, True, True),
        (34, False, True, True),
    ],
    "repeated_motion": [
        (0, True, True, True),
        (20, True, True, True),
        (49, False, True, True),
        (51, False, True, True),
    ],
    "fault_recovery": [
        (0, True, True, True),
        (1, False, True, False),
        (2, False, True, True),
        (5, False, True, True),
    ],
    "day_to_night": [
        (0, False, False, True),
        (1, False, True, True),
        (2, True, True, True),
    ],
}


def main():
    controller = LightingController()
    rows = []

    lamps = [
        ("P1", "walking_path"),
        ("E1", "habitat_edge"),
        ("H1", "habitat_corridor"),
    ]

    print(
        "SIMULATED INPUTS - illustrative settings; "
        "no AI training"
    )

    for scenario, events in SCENARIOS.items():
        controller.reset()
        print(f"\nScenario: {scenario}")

        for t, motion, night, healthy in events:
            for lamp, zone in lamps:
                reading = SensorInput(
                    lamp_id=lamp,
                    zone=zone,
                    time_s=t,
                    motion=motion,
                    is_night=night,
                    sensor_ok=healthy,
                )

                decision = controller.update(reading)

                print(
                    f"{t:>3}s | "
                    f"{zone:<17} | "
                    f"{decision.brightness_pct:>5.1f}% | "
                    f"{decision.mode:<9} | "
                    f"{decision.reason}"
                )

                rows.append({
                    "scenario": scenario,
                    "data_source": "synthetic_rule_scenario",
                    **asdict(reading),
                    **asdict(decision),
                })

    path = (LOG_DIR / "controller_demo_log.csv")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"\nSaved {len(rows)} decisions to {path.name}"
    )


if __name__ == "__main__":
    main()