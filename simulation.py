"""Connect the NightWise environment, agents, sensors and controller."""
from controller import SensorInput
from models import estimate_power_w, estimate_point_lux
from dataclasses import asdict

from agents import Agent
from controller import LightingController
from environment import load_environment
from sensors import create_sensor_reading


class Simulation:
    def __init__(self, agents, config_path=None):
        self.environment = load_environment(config_path)
        self.agents = list(agents)
        self.controller = LightingController()
        self.last_time_s = None
        self.sensor_samples = {}
        self.sensor_stale_timeout_s = self.environment[
            "sensor_stale_timeout_s"
        ]

    def reset(self):
        """Reset controller memory before replaying from time zero."""
        self.controller.reset()
        self.last_time_s = None
        self.sensor_samples.clear()

    def step(self, time_s, is_night=True, faulty_lamp_ids=None, stale_lamp_ids=None,):
        """Advance the simulation and return this frame's data."""
        # Validate before updating any lamp.
        import math

        if (
            isinstance(time_s, bool)
            or not isinstance(time_s, (int, float))
            or not math.isfinite(time_s)
            or time_s < 0
        ):
            raise ValueError("Time must be finite and nonnegative.")

        if self.last_time_s is not None and time_s <= self.last_time_s:
            raise ValueError("Time must increase; reset before replay.")

        if type(is_night) is not bool:
            raise ValueError("is_night must be a Boolean.")

        faulty_lamp_ids = (
            set() if faulty_lamp_ids is None
            else set(faulty_lamp_ids)
        )

        known_lamp_ids = {
            lamp["lamp_id"]
            for lamp in self.environment["lamps"]
        }

        unknown_ids = faulty_lamp_ids - known_lamp_ids

        if unknown_ids:
            raise ValueError(
                f"Unknown faulty lamp IDs: {sorted(unknown_ids)}"
            )

        stale_lamp_ids = (
            set() if stale_lamp_ids is None
            else set(stale_lamp_ids)
        )

        unknown_stale_ids = stale_lamp_ids - known_lamp_ids

        if unknown_stale_ids:
            raise ValueError(
                f"Unknown stale lamp IDs: {sorted(unknown_stale_ids)}"
            )

        agent_positions = []

        for agent in self.agents:
            position = agent.position_at(time_s)

            if position is not None:
                x, y = position
                agent_positions.append({
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "x_m": x,
                    "y_m": y,
                })

        lamp_results = []

        for lamp in self.environment["lamps"]:
            lamp_id = lamp["lamp_id"]

            # Receive a fresh motion sample unless communication is blocked.
            if lamp_id not in stale_lamp_ids:
                fresh_reading = create_sensor_reading(
                    lamp=lamp,
                    agents=self.agents,
                    time_s=time_s,
                    is_night=is_night,
                )

                self.sensor_samples[lamp_id] = {
                    "sample_time_s": time_s,
                    "motion": fresh_reading.motion,
                }

            sample = self.sensor_samples.get(lamp_id)

            sample_age_s = (
                None
                if sample is None
                else time_s - sample["sample_time_s"]
            )

            sample_is_fresh = (
                sample_age_s is not None
                and sample_age_s <= self.sensor_stale_timeout_s
            )

            sensor_ok = (
                lamp_id not in faulty_lamp_ids
                and sample_is_fresh
            )

            if lamp_id in faulty_lamp_ids:
                sensor_status = "fault"
            elif sample is None:
                sensor_status = "missing"
            elif not sample_is_fresh:
                sensor_status = "stale"
            else:
                sensor_status = "healthy"

            reading = SensorInput(
                lamp_id=lamp_id,
                zone=lamp["zone"],
                time_s=time_s,
                motion=sample["motion"] if sensor_ok else False,
                is_night=is_night,
                sensor_ok=sensor_ok,
            )

            decision = self.controller.update(reading)

            power_w = estimate_power_w(
                rated_power_w=lamp["rated_power_w"],
                brightness_pct=decision.brightness_pct,
            )

            lamp_results.append({
                **asdict(reading),
                **asdict(decision),
                "sensor_status": sensor_status,
                "sample_age_s": sample_age_s,
                "power_w": power_w,
            })

        brightness_by_id = {
            lamp["lamp_id"]: lamp["brightness_pct"]
            for lamp in lamp_results
        }

        lux_readings = []

        for point in self.environment["measurement_points"]:
            artificial_lux = estimate_point_lux(
                lamps=self.environment["lamps"],
                brightness_by_id=brightness_by_id,
                point=point,
            )

            lux_readings.append({
                "point_id": point["point_id"],
                "zone": point["zone"],
                "x_m": point["x_m"],
                "y_m": point["y_m"],
                "artificial_lux": artificial_lux,
            })
        
        self.last_time_s = time_s


        return {
            "data_source": "simulated",
            "time_s": time_s,
            "agents": agent_positions,
            "lamps": lamp_results,
            "total_power_w": sum(
                lamp["power_w"] for lamp in lamp_results
            ),
            "lux_readings": lux_readings,
        }


def main():
    pedestrian = Agent(
        agent_id="PERSON_1",
        agent_type="person",
        route=((0.0, 10.0), (60.0, 10.0)),
        speed_m_s=1.2,
        start_time_s=5.0,
    )

    simulation = Simulation(agents=[pedestrian])

    # Print selected snapshots, but update the controller every second.
    snapshot_times = {0, 10, 20, 30, 40, 50, 55, 60, 70, 80, 90}

    print("NIGHTWISE — SIMULATED LIGHTING")
    print("Time | Lamp | Motion | Brightness | Power | Mode")

    for time_s in range(91):
        frame = simulation.step(time_s)

        if time_s in snapshot_times:
            for lamp in frame["lamps"]:
                print(
                    f"{time_s:>4}s | "
                    f"{lamp['lamp_id']:<4} | "
                    f"{str(lamp['motion']):<6} | "
                    f"{lamp['brightness_pct']:>9.1f}% | "
                    f"{lamp['power_w']:>5.1f} W | "
                    f"{lamp['mode']}"
                )


    print("\nARTIFICIAL LIGHT AT MEASUREMENT POINTS")

    simulation.reset()

    for time_s in range(11):
        frame = simulation.step(time_s)

        if time_s in (0, 10):
            print(f"\nTime: {time_s}s")

            for point in frame["lux_readings"]:
                print(
                    f"  {point['point_id']}: "
                    f"{point['artificial_lux']:.3f} lux"
                )


if __name__ == "__main__":
    main()