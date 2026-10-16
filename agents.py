"""Repeatable moving agents for the NightWise simulation."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Agent:
    agent_id: str
    agent_type: str
    route: tuple[tuple[float, float], ...]
    speed_m_s: float
    start_time_s: float = 0.0

    def __post_init__(self):
        if len(self.route) < 2:
            raise ValueError("An agent route needs at least two points.")

        if not math.isfinite(self.speed_m_s) or self.speed_m_s <= 0:
            raise ValueError("Agent speed must be finite and positive.")

        if not math.isfinite(self.start_time_s) or self.start_time_s < 0:
            raise ValueError("Start time must be finite and nonnegative.")

        for point in self.route:
            if len(point) != 2 or not all(
                math.isfinite(value) for value in point
            ):
                raise ValueError("Route points need finite x and y values.")

        if self.route_length_m == 0:
            raise ValueError("The route must have a positive length.")

    @property
    def route_length_m(self):
        """Total distance along all route segments."""
        return sum(
            math.dist(start, end)
            for start, end in zip(self.route, self.route[1:])
        )

    @property
    def end_time_s(self):
        return self.start_time_s + self.route_length_m / self.speed_m_s

    def position_at(self, time_s):
        """Return (x, y), or None before entry and after departure."""
        if not math.isfinite(time_s) or time_s < 0:
            raise ValueError("Simulation time must be finite and nonnegative.")

        # The agent leaves the environment when its route ends.
        if time_s < self.start_time_s or time_s >= self.end_time_s:
            return None

        remaining_distance = (
            time_s - self.start_time_s
        ) * self.speed_m_s

        for start, end in zip(self.route, self.route[1:]):
            segment_length = math.dist(start, end)

            if segment_length == 0:
                continue

            if remaining_distance <= segment_length:
                fraction = remaining_distance / segment_length

                x = start[0] + fraction * (end[0] - start[0])
                y = start[1] + fraction * (end[1] - start[1])

                return x, y

            remaining_distance -= segment_length

        return None


def main():
    pedestrian = Agent(
        agent_id="PERSON_1",
        agent_type="person",
        route=((0.0, 10.0), (60.0, 10.0)),
        speed_m_s=1.2,
        start_time_s=5.0,
    )

    print(f"Agent: {pedestrian.agent_id}")
    print(f"Route length: {pedestrian.route_length_m:.1f} m")
    print(f"Entry time: {pedestrian.start_time_s:.1f} s")
    print(f"Departure time: {pedestrian.end_time_s:.1f} s")

    for time_s in (0, 5, 10, 20, 30, 40, 50, 55, 60):
        position = pedestrian.position_at(time_s)

        if position is None:
            print(f"{time_s:>3}s | outside environment")
        else:
            x, y = position
            print(f"{time_s:>3}s | x={x:.1f} m, y={y:.1f} m")


if __name__ == "__main__":
    main()