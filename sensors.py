"""Simulated movement sensors for NightWise."""

import math

from agents import Agent
from controller import SensorInput
from environment import load_environment


def detects_motion(lamp, agents, time_s):
    """Detect moving agents inside this lamp's circular sensor range."""
    lamp_position = (lamp["x_m"], lamp["y_m"])
    radius = lamp["sensor_radius_m"]

    for agent in agents:
        position = agent.position_at(time_s)

        if position is None:
            continue

        # Current agents move continuously while active.
        # Agent type is deliberately not used for detection.
        distance = math.dist(lamp_position, position)

        if distance <= radius:
            return True

    return False


def create_sensor_reading(
    lamp,
    agents,
    time_s,
    is_night=True,
    sensor_ok=True,
):
    """Build the input expected by Person 1's controller."""
    return SensorInput(
        lamp_id=lamp["lamp_id"],
        zone=lamp["zone"],
        time_s=time_s,
        motion=detects_motion(lamp, agents, time_s),
        is_night=is_night,
        sensor_ok=sensor_ok,
    )


def main():
    environment = load_environment()

    pedestrian = Agent(
        agent_id="PERSON_1",
        agent_type="person",
        route=((0.0, 10.0), (60.0, 10.0)),
        speed_m_s=1.2,
        start_time_s=5.0,
    )

    agents = [pedestrian]

    print("SIMULATED MOTION SENSORS")
    print("Detection includes the sensor-range boundary.")

    for time_s in (0, 5, 10, 20, 30, 40, 50, 55):
        position = pedestrian.position_at(time_s)

        if position is None:
            print(f"\nTime: {time_s}s | Agent outside environment")
        else:
            x, y = position
            print(
                f"\nTime: {time_s}s | "
                f"Agent position: ({x:.1f}, {y:.1f}) m"
            )

        for lamp in environment["lamps"]:
            reading = create_sensor_reading(
                lamp=lamp,
                agents=agents,
                time_s=time_s,
            )

            print(
                f"  {reading.lamp_id}: motion={reading.motion}"
            )


if __name__ == "__main__":
    main()