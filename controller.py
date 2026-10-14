"""Rule-based simulation controller.

Settings are illustrative, not real-world deployment standards.
Requires Python 3.10 or newer.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import math


def number(value, name, minimum=0, maximum=None):
    """Validate a finite numeric value within the permitted range."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")

    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be <= {maximum}")

    return float(value)


@dataclass(frozen=True)
class ZoneProfile:
    idle: float
    occupied: float
    fallback: float
    cap: float


@dataclass(frozen=True)
class SensorInput:
    lamp_id: str
    zone: str
    time_s: float
    motion: bool
    is_night: bool
    sensor_ok: bool = True


@dataclass(frozen=True)
class Decision:
    lamp_id: str
    zone: str
    brightness_pct: float
    mode: str
    reason: str


@dataclass(frozen=True)
class _State:
    """Internal memory for one lamp."""

    zone: str
    time_s: float
    brightness: float
    last_motion: float | None


class LightingController:
    def __init__(self, config_path=None):
        # Find the configuration beside this file by default.
        path = (
            Path(config_path)
            if config_path
            else Path(__file__).with_name("controller_config.json")
        )

        with path.open(encoding="utf-8") as file:
            config = json.load(file)

        self.hold_seconds = number(
            config["hold_seconds"],
            "hold_seconds",
        )

        self.fade_rate = number(
            config["fade_pct_per_second"],
            "fade rate",
        )

        if self.fade_rate == 0:
            raise ValueError("fade rate must be positive")

        expected = {
            "walking_path",
            "habitat_edge",
            "habitat_corridor",
        }

        if set(config["zones"]) != expected:
            raise ValueError(
                "Configuration must contain the three supported zones"
            )

        self.profiles = {}

        for zone, values in config["zones"].items():
            profile = ZoneProfile(
                **{
                    key: number(
                        values[key],
                        f"{zone}.{key}",
                        maximum=100,
                    )
                    for key in (
                        "idle",
                        "occupied",
                        "fallback",
                        "cap",
                    )
                }
            )

            if not profile.idle <= profile.occupied <= profile.cap:
                raise ValueError(
                    f"{zone}: require idle <= occupied <= cap"
                )

            if profile.fallback > profile.cap:
                raise ValueError(
                    f"{zone}: fallback exceeds cap"
                )

            if (
                zone == "habitat_corridor"
                and any(vars(profile).values())
            ):
                raise ValueError(
                    "Habitat corridor must remain unlit"
                )

            self.profiles[zone] = profile

        self._states = {}

    def reset(self):
        """Clear lamp memory before replaying a scenario."""
        self._states.clear()

    def _validate(self, reading):
        """Validate input without changing controller state."""
        if not isinstance(reading, SensorInput):
            raise ValueError("Expected a SensorInput object")

        if (
            not isinstance(reading.lamp_id, str)
            or not reading.lamp_id.strip()
        ):
            raise ValueError(
                "lamp_id must be a nonempty string"
            )

        if (
            not isinstance(reading.zone, str)
            or reading.zone not in self.profiles
        ):
            raise ValueError("Unknown zone")

        number(reading.time_s, "time_s")

        flags = (
            reading.motion,
            reading.is_night,
            reading.sensor_ok,
        )

        if any(type(flag) is not bool for flag in flags):
            raise ValueError(
                "Sensor flags must be booleans"
            )

        previous = self._states.get(reading.lamp_id)

        if previous and previous.zone != reading.zone:
            raise ValueError(
                "Lamp zone cannot change without reset"
            )

        if previous and reading.time_s <= previous.time_s:
            raise ValueError(
                "Time must increase per lamp; reset before replay"
            )

        return previous

    def _night_decision(self, reading, profile, previous):
        """Apply movement, hold and fade rules at night."""
        last_motion = (
            previous.last_motion
            if previous
            else None
        )

        if reading.motion:
            last_motion = reading.time_s

        within_hold = (
            last_motion is not None
            and reading.time_s
            <= last_motion + self.hold_seconds
        )

        if within_hold:
            return (
                profile.occupied,
                "occupied",
                "Motion or hold period",
                last_motion,
            )

        old_brightness = (
            previous.brightness
            if previous
            else profile.idle
        )

        fade_start = (
            previous.time_s
            if previous
            else reading.time_s
        )

        # Only count time after the hold period ends.
        if last_motion is not None:
            fade_start = max(
                fade_start,
                last_motion + self.hold_seconds,
            )

        elapsed = max(
            0,
            reading.time_s - fade_start,
        )

        brightness = max(
            profile.idle,
            old_brightness - self.fade_rate * elapsed,
        )

        mode = (
            "fading"
            if brightness > profile.idle
            else "idle"
        )

        reason = (
            "Gradual dimming"
            if mode == "fading"
            else "No recent motion"
        )

        return brightness, mode, reason, last_motion

    def update(self, reading: SensorInput) -> Decision:
        """Process one reading and return a lamp decision."""
        previous = self._validate(reading)
        profile = self.profiles[reading.zone]

        # Fault handling takes priority over daytime.
        if not reading.sensor_ok:
            result = (
                profile.fallback,
                "fallback",
                "Sensor fault",
                None,
            )

        elif not reading.is_night:
            result = (
                0,
                "daylight",
                "Daytime: lamp off",
                None,
            )

        elif reading.zone == "habitat_corridor":
            result = (
                0,
                "protected",
                "Unlit habitat zone",
                None,
            )

        else:
            result = self._night_decision(
                reading,
                profile,
                previous,
            )

        brightness, mode, reason, last_motion = result

        # Enforce the zone's output limit.
        brightness = min(
            profile.cap,
            max(0, brightness),
        )

        self._states[reading.lamp_id] = _State(
            zone=reading.zone,
            time_s=reading.time_s,
            brightness=brightness,
            last_motion=last_motion,
        )

        return Decision(
            lamp_id=reading.lamp_id,
            zone=reading.zone,
            brightness_pct=round(brightness, 2),
            mode=mode,
            reason=reason,
        )