"""Validate simulation inputs before calculating impact."""

import math


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