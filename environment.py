"""Fictional township layout for the NightWise simulation."""

import json
from pathlib import Path


def load_environment(config_path=None):
    """Load the environment configuration."""
    path = (
        Path(config_path)
        if config_path is not None
        else Path(__file__).with_name("environment_config.json")
    )

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def main():
    environment = load_environment()

    print(f"Environment: {environment['name']}")
    print(
        f"Size: {environment['width_m']} m "
        f"x {environment['height_m']} m"
    )

    print("\nZones:")
    for zone in environment["zones"]:
        print(f"  {zone['zone_id']}: {zone['bounds_m']}")

    print("\nLamps:")
    for lamp in environment["lamps"]:
        print(
            f"  {lamp['lamp_id']} | {lamp['zone']} | "
            f"position=({lamp['x_m']}, {lamp['y_m']}) m | "
            f"sensor radius={lamp['sensor_radius_m']} m"
        )

    print("\nMeasurement points:")
    for point in environment["measurement_points"]:
        print(
            f"  {point['point_id']} | {point['zone']} | "
            f"position=({point['x_m']}, {point['y_m']}) m"
        )


if __name__ == "__main__":
    main()