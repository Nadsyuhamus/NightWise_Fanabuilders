"""Validate simulation inputs before calculating impact."""

import math
from copy import deepcopy

TIME_TOLERANCE_S = 1e-9


def _number(value, label, minimum=0.0):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < minimum
    ):
        raise ValueError(
            f"{label} must be a finite number >= {minimum}"
        )
    return value


def validate_intervals(frames):
    """Require ordered, continuous, non-overlapping intervals.

    Each frame applies over [time_s, time_s + dt_s).
    Variable interval durations are allowed.
    """
    if not frames:
        raise ValueError("Run contains no frames")

    previous_end = None

    for index, frame in enumerate(frames):
        label = f"Frame {index}"

        for key in ("time_s", "dt_s", "total_power_w"):
            if key not in frame:
                raise ValueError(f"{label}: missing {key}")

        start = _number(frame["time_s"], f"{label} time_s")
        duration = _number(frame["dt_s"], f"{label} dt_s")
        _number(frame["total_power_w"], f"{label} total_power_w")

        if duration == 0:
            raise ValueError(f"{label}: dt_s must be positive")

        end = start + duration

        if not math.isfinite(end) or end <= start:
            raise ValueError(f"{label}: invalid interval end")

        if previous_end is not None and not math.isclose(
            start,
            previous_end,
            rel_tol=0.0,
            abs_tol=TIME_TOLERANCE_S,
        ):
            problem = (
                "gap / missing interval"
                if start > previous_end
                else "duplicate, overlapping, or unordered interval"
            )
            raise ValueError(
                f"{label}: {problem}; "
                f"expected start {previous_end}, got {start}"
            )

        previous_end = end


def _records_by_id(records, id_key, label):
    if not isinstance(records, list):
        raise ValueError(f"{label} must be a list")

    indexed = {}

    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"{label}: record must be a dictionary")

        identifier = record.get(id_key)

        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{label}: invalid or missing {id_key}")

        if identifier in indexed:
            raise ValueError(
                f"{label}: duplicate {id_key} {identifier}"
            )

        indexed[identifier] = record

    return indexed


def _require_ids(actual, expected, label):
    missing = set(expected) - set(actual)
    unexpected = set(actual) - set(expected)

    if missing or unexpected:
        raise ValueError(
            f"{label}: missing={sorted(missing)}, "
            f"unexpected={sorted(unexpected)}"
        )


def validate_run(
    frames,
    environment,
    *,
    expected_start_s,
    expected_end_s,
):
    """Validate a complete run against independent expected metadata."""
    validate_intervals(frames)

    expected_start_s = _number(
        expected_start_s, "Expected start"
    )
    expected_end_s = _number(
        expected_end_s, "Expected end"
    )

    if expected_end_s <= expected_start_s:
        raise ValueError("Expected end must be after expected start")

    actual_start = frames[0]["time_s"]
    actual_end = frames[-1]["time_s"] + frames[-1]["dt_s"]

    for label, actual, expected in (
        ("Run start", actual_start, expected_start_s),
        ("Run end", actual_end, expected_end_s),
    ):
        if not math.isclose(
            actual,
            expected,
            rel_tol=0.0,
            abs_tol=TIME_TOLERANCE_S,
        ):
            raise ValueError(
                f"{label}: expected {expected}, got {actual}"
            )

    expected_lamps = _records_by_id(
        environment["lamps"], "lamp_id", "Environment lamps"
    )
    expected_points = _records_by_id(
        environment["measurement_points"],
        "point_id",
        "Environment points",
    )

    for index, frame in enumerate(frames):
        label = f"Frame {index}"

        lamps = _records_by_id(
            frame.get("lamps"), "lamp_id", f"{label} lamps"
        )
        points = _records_by_id(
            frame.get("lux_readings"),
            "point_id",
            f"{label} points",
        )

        _require_ids(lamps, expected_lamps, f"{label} lamps")
        _require_ids(points, expected_points, f"{label} points")

        night_states = set()

        for lamp_id, lamp in lamps.items():
            power = _number(
                lamp.get("power_w"),
                f"{label} {lamp_id} power_w",
            )
            brightness = _number(
                lamp.get("brightness_pct"),
                f"{label} {lamp_id} brightness_pct",
            )

            if brightness > 100:
                raise ValueError(
                    f"{label} {lamp_id}: brightness exceeds 100%"
                )

            if not isinstance(lamp.get("is_night"), bool):
                raise ValueError(
                    f"{label} {lamp_id}: is_night must be boolean"
                )

            night_states.add(lamp["is_night"])

        if len(night_states) != 1:
            raise ValueError(
                f"{label}: expected one shared day/night state"
            )

        lamp_total = sum(
            lamp["power_w"] for lamp in lamps.values()
        )

        if not math.isfinite(lamp_total) or not math.isclose(
            lamp_total,
            frame["total_power_w"],
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{label}: total_power_w differs from lamp sum"
            )

        for point_id, point in points.items():
            _number(
                point.get("artificial_lux"),
                f"{label} {point_id} artificial_lux",
            )

def validate_fair_comparison(adaptive_frames, baseline_frames):
    """Require matched conditions while allowing policy outputs to differ."""
    if not adaptive_frames or not baseline_frames:
        raise ValueError("Comparison requires two non-empty runs")

    if len(adaptive_frames) != len(baseline_frames):
        raise ValueError("Comparison frame counts differ")

    context = adaptive_frames[0].get("comparison_context")

    if not isinstance(context, dict):
        raise ValueError("Missing comparison context; regenerate the runs")

    # Snapshot so every subsequent frame is checked against one reference.
    context = deepcopy(context)

    required_context = (
        "schema_version",
        "model_version",
        "interval_convention",
        "baseline_definition",
        "environment",
        "controller",
    )

    for key in required_context:
        if key not in context:
            raise ValueError(f"Missing comparison context field: {key}")

    if context["baseline_definition"] != "fixed_nighttime_zone_cap":
        raise ValueError("Unsupported baseline definition")

    if context["interval_convention"] != "[time_s, time_s + dt_s)":
        raise ValueError("Unsupported interval convention")

    environment = context["environment"]
    controller = context["controller"]

    fixtures = _records_by_id(
        environment["lamps"], "lamp_id", "Environment lamps"
    )
    points = _records_by_id(
        environment["measurement_points"],
        "point_id",
        "Environment points",
    )

    if not fixtures or not points:
        raise ValueError("Comparison requires fixtures and measurement points")

    # Validate each complete sequence before comparing individual frames.
    validate_intervals(adaptive_frames)
    validate_intervals(baseline_frames)

    expected_start = adaptive_frames[0]["time_s"]
    expected_end = (
        adaptive_frames[-1]["time_s"] + adaptive_frames[-1]["dt_s"]
    )

    for frames in (adaptive_frames, baseline_frames):
        validate_run(
            frames,
            environment,
            expected_start_s=expected_start,
            expected_end_s=expected_end,
        )

    input_fields = (
        "zone",
        "time_s",
        "motion",
        "is_night",
        "sensor_ok",
        "daylight_ok",
        "sensor_status",
        "sample_age_s",
    )

    for index, (adaptive, baseline) in enumerate(
        zip(adaptive_frames, baseline_frames)
    ):
        for field in ("time_s", "dt_s"):
            if adaptive[field] != baseline[field]:
                raise ValueError(
                    f"Frame {index}: comparison {field} differs"
                )

        for field in ("scenario", "agents"):
            if field not in adaptive or field not in baseline:
                raise ValueError(f"Frame {index}: missing {field}")

            if adaptive[field] != baseline[field]:
                raise ValueError(
                    f"Frame {index}: comparison {field} differs"
                )

        lamp_sets = []

        for frame in (adaptive, baseline):
            if frame.get("data_source") != "simulated":
                raise ValueError(
                    f"Frame {index}: expected simulated data"
                )

            if frame.get("comparison_context") != context:
                raise ValueError(
                    f"Frame {index}: comparison configuration differs"
                )

            lamps = _records_by_id(
                frame["lamps"], "lamp_id", f"Frame {index} lamps"
            )
            readings = _records_by_id(
                frame["lux_readings"],
                "point_id",
                f"Frame {index} points",
            )

            for lamp_id, lamp in lamps.items():
                if lamp.get("zone") != fixtures[lamp_id]["zone"]:
                    raise ValueError(
                        f"Frame {index}: fixture zone differs for {lamp_id}"
                    )

            for point_id, reading in readings.items():
                for field in ("zone", "x_m", "y_m"):
                    if reading.get(field) != points[point_id][field]:
                        raise ValueError(
                            f"Frame {index}: measurement geometry differs "
                            f"for {point_id}.{field}"
                        )

            lamp_sets.append(lamps)

        adaptive_lamps, baseline_lamps = lamp_sets

        for lamp_id, fixture in fixtures.items():
            adaptive_lamp = adaptive_lamps[lamp_id]
            baseline_lamp = baseline_lamps[lamp_id]

            for field in input_fields:
                if (
                    field not in adaptive_lamp
                    or field not in baseline_lamp
                ):
                    raise ValueError(
                        f"Frame {index}: missing {lamp_id}.{field}"
                    )

                if adaptive_lamp[field] != baseline_lamp[field]:
                    raise ValueError(
                        f"Frame {index}: input differs for "
                        f"{lamp_id}.{field}"
                    )

            zone = fixture["zone"]
            expected_brightness = (
                controller["zones"][zone]["cap"]
                if baseline_lamp["is_night"]
                else 0.0
            )

            if baseline_lamp["brightness_pct"] != expected_brightness:
                raise ValueError(
                    f"Frame {index}: baseline policy differs for {lamp_id}"
                )