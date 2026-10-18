"""Illustrative physical models for the NightWise simulation."""

import math


def estimate_power_w(rated_power_w, brightness_pct):
    """Estimate lamp power using a proportional brightness model."""
    for name, value in (
        ("rated_power_w", rated_power_w),
        ("brightness_pct", brightness_pct),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number.")

    if rated_power_w <= 0:
        raise ValueError("Rated power must be positive.")

    if not 0 <= brightness_pct <= 100:
        raise ValueError("Brightness must be between 0 and 100.")

    return rated_power_w * brightness_pct / 100


def estimate_lamp_lux(lamp, brightness_pct, point):
    """Estimate one lamp's artificial illuminance at a ground point."""
    # Reuse brightness validation from the power model.
    estimate_power_w(lamp["rated_power_w"], brightness_pct)

    height = lamp["height_m"]
    full_output_lux = lamp["full_output_lux_below"]
    spill_factor = lamp["habitat_spill_factor"]

    for name, value in (
        ("height_m", height),
        ("full_output_lux_below", full_output_lux),
        ("habitat_spill_factor", spill_factor),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number.")

    if height <= 0:
        raise ValueError("Lamp height must be positive.")

    if full_output_lux < 0:
        raise ValueError("Full-output lux must be nonnegative.")

    if not 0 <= spill_factor <= 1:
        raise ValueError("Habitat spill factor must be between 0 and 1.")

    distance_m = math.dist(
        (lamp["x_m"], lamp["y_m"]),
        (point["x_m"], point["y_m"]),
    )

    attenuation = height**2 / (height**2 + distance_m**2)

    habitat_point = point["zone"] in (
        "habitat_edge",
        "habitat_corridor",
    )

    directional_factor = spill_factor if habitat_point else 1.0

    return (
        full_output_lux
        * brightness_pct / 100
        * attenuation
        * directional_factor
    )


def estimate_point_lux(lamps, brightness_by_id, point):
    """Sum contributions from every lamp at one measurement point."""
    return sum(
        estimate_lamp_lux(
            lamp,
            brightness_by_id[lamp["lamp_id"]],
            point,
        )
        for lamp in lamps
    )


def main():
    print("SIMULATED POWER — 40 W FIXTURE")

    for brightness in (0, 10, 30, 50, 70, 100):
        power = estimate_power_w(40, brightness)
        print(f"{brightness:>3}% brightness -> {power:.1f} W")


if __name__ == "__main__":
    main()