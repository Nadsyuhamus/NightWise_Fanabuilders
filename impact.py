"""Shared baseline and impact calculations for simulated NightWise runs."""

from copy import deepcopy
from models import estimate_power_w, estimate_point_lux

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

def total_energy_kwh(frames):
    """Integrate power over each logged interval."""
    return sum(
        frame["total_power_w"] * frame["dt_s"]
        for frame in frames
    ) / 3_600_000


def reduction_pct(baseline, adaptive):
    """Return percentage reduction; undefined when baseline is zero."""
    if baseline == 0:
        return None

    return 100 * (baseline - adaptive) / baseline


def compare_energy(adaptive_frames, baseline_frames):
    """Calculate energy metrics for matching simulation intervals."""
    if len(adaptive_frames) != len(baseline_frames):
        raise ValueError("Comparison frame counts differ")

    for adaptive, fixed in zip(adaptive_frames, baseline_frames):
        adaptive_interval = (adaptive["time_s"], adaptive["dt_s"])
        fixed_interval = (fixed["time_s"], fixed["dt_s"])

        if adaptive_interval != fixed_interval:
            raise ValueError("Comparison intervals differ")

    adaptive = total_energy_kwh(adaptive_frames)
    baseline = total_energy_kwh(baseline_frames)

    return {
        "adaptive_kwh": adaptive,
        "baseline_kwh": baseline,
        "saved_kwh": baseline - adaptive,
        "savings_pct": reduction_pct(baseline, adaptive),
    }


def mean_point_lux(frames, point_ids, night_only=True):
    """Return duration-weighted mean artificial lux for each point.

    None means there were no eligible readings.
    """
    exposure = {point_id: 0.0 for point_id in point_ids}
    duration = {point_id: 0.0 for point_id in point_ids}

    for frame in frames:
        if night_only and not any(
            lamp["is_night"] for lamp in frame["lamps"]
        ):
            continue

        for point in frame["lux_readings"]:
            point_id = point["point_id"]

            if point_id in exposure:
                exposure[point_id] += (
                    point["artificial_lux"] * frame["dt_s"]
                )
                duration[point_id] += frame["dt_s"]

    return {
        point_id: (
            exposure[point_id] / duration[point_id]
            if duration[point_id] > 0
            else None
        )
        for point_id in exposure
    }