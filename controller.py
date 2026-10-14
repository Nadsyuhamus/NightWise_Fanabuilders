"""NightWise rule-based lighting controller.

Settings are illustrative for simulation, not real-world lighting standards.
Requires Python 3.10 or newer.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ZoneProfile:
    idle: float
    occupied: float
    fallback: float


# Brightness percentages for each zone.
PROFILES = {
    "walking_path": ZoneProfile(
        idle=30,
        occupied=70,
        fallback=50,
    ),
    "habitat_edge": ZoneProfile(
        idle=10,
        occupied=30,
        fallback=20,
    ),
    # This habitat zone is not a pedestrian route.
    "habitat_corridor": ZoneProfile(
        idle=0,
        occupied=0,
        fallback=0,
    ),
}


@dataclass(frozen=True)
class SensorInput:
    lamp_id: str
    zone: str
    time_s: float  # Simulation seconds, not your computer's clock.
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


@dataclass
class _State:
    """Internal memory for one lamp."""

    zone: str
    time_s: float
    brightness: float
    last_motion: float | None = None


class LightingController:
    def __init__(
        self,
        hold_seconds=30.0,
        fade_pct_per_second=10.0,
    ):
        if not math.isfinite(hold_seconds) or hold_seconds < 0:
            raise ValueError(
                "hold_seconds must be finite and nonnegative"
            )

        if (
            not math.isfinite(fade_pct_per_second)
            or fade_pct_per_second <= 0
        ):
            raise ValueError(
                "fade rate must be finite and positive"
            )

        self.hold_seconds = hold_seconds
        self.fade_rate = fade_pct_per_second

        # Each lamp has its own movement history and brightness.
        self._states: dict[str, _State] = {}

    def reset(self):
        """Clear lamp memory before replaying a scenario."""
        self._states.clear()

    def update(self, reading: SensorInput) -> Decision:
        """Read sensor inputs and return a lighting decision."""

        # Validate the input.
        if reading.zone not in PROFILES:
            raise ValueError(f"Unknown zone: {reading.zone}")

        if (
            not reading.lamp_id
            or not math.isfinite(reading.time_s)
            or reading.time_s < 0
        ):
            raise ValueError(
                "Provide a lamp_id and finite nonnegative time_s"
            )

        for flag in (
            reading.motion,
            reading.is_night,
            reading.sensor_ok,
        ):
            if type(flag) is not bool:
                raise ValueError(
                    "Sensor flags must be booleans"
                )

        profile = PROFILES[reading.zone]
        previous = self._states.get(reading.lamp_id)

        if previous and (
            previous.zone != reading.zone
            or reading.time_s <= previous.time_s
        ):
            raise ValueError(
                "Keep zone fixed and time increasing per lamp; "
                "reset for replay"
            )

        # Elapsed time since this lamp's previous reading.
        dt = (
            reading.time_s - previous.time_s
            if previous
            else 0
        )

        state = previous or _State(
            zone=reading.zone,
            time_s=reading.time_s,
            brightness=profile.idle,
        )

        # Rule 1: Fault handling takes priority.
        if not reading.sensor_ok:
            brightness = profile.fallback
            mode = "fallback"
            reason = "Sensor fault"
            state.last_motion = None

        # Rule 2: Healthy sensors report daytime.
        elif not reading.is_night:
            brightness = 0
            mode = "daylight"
            reason = "Daytime: lamp off"
            state.last_motion = None

        # Rule 3: Keep the habitat corridor unlit.
        elif reading.zone == "habitat_corridor":
            brightness = 0
            mode = "protected"
            reason = "Unlit habitat zone"
            state.last_motion = None

        # Rule 4: Control path and habitat-edge lighting.
        else:
            if reading.motion:
                state.last_motion = reading.time_s

            within_hold = (
                state.last_motion is not None
                and reading.time_s
                <= state.last_motion + self.hold_seconds
            )

            if within_hold:
                brightness = profile.occupied
                mode = "occupied"
                reason = "Motion or hold period"

            else:
                # Count only the time after the hold expires.
                fade_dt = dt

                if (
                    state.last_motion is not None
                    and previous is not None
                ):
                    hold_end = (
                        state.last_motion + self.hold_seconds
                    )
                    fade_start = max(
                        previous.time_s,
                        hold_end,
                    )
                    fade_dt = max(
                        0,
                        reading.time_s - fade_start,
                    )

                # Never fade below the zone's idle brightness.
                brightness = max(
                    profile.idle,
                    state.brightness
                    - self.fade_rate * fade_dt,
                )

                if brightness > profile.idle:
                    mode = "fading"
                    reason = "Gradual dimming"
                else:
                    mode = "idle"
                    reason = "No recent motion"

        # Save memory for the next reading.
        state.brightness = brightness
        state.time_s = reading.time_s
        self._states[reading.lamp_id] = state

        return Decision(
            lamp_id=reading.lamp_id,
            zone=reading.zone,
            brightness_pct=round(brightness, 2),
            mode=mode,
            reason=reason,
        )