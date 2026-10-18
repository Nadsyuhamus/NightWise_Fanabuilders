"""Repeatable synthetic scenarios for NightWise."""

from dataclasses import dataclass

from agents import Agent


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    duration_s: int
    agents: tuple[Agent, ...] = ()
    night_windows: tuple[tuple[int, int], ...] = ((0, 120),)
    fault_windows: tuple[tuple[str, int, int], ...] = ()
    stale_windows: tuple[tuple[str, int, int], ...] = ()

    def conditions_at(self, time_s):
        """Return conditions for intervals with start <= time < end."""
        return {
            "is_night": any(
                start <= time_s < end
                for start, end in self.night_windows
            ),
            "faulty_lamp_ids": {
                lamp_id
                for lamp_id, start, end in self.fault_windows
                if start <= time_s < end
            },
            "stale_lamp_ids": {
                lamp_id
                for lamp_id, start, end in self.stale_windows
                if start <= time_s < end
            },
        }


def pedestrian(agent_id="PERSON_1", start_time_s=5.0):
    return Agent(
        agent_id=agent_id,
        agent_type="person",
        route=((0.0, 10.0), (60.0, 10.0)),
        speed_m_s=1.2,
        start_time_s=start_time_s,
    )


def get_scenarios():
    """Return fresh scenario definitions."""
    return {
        "empty_night": Scenario(
            name="empty_night",
            description="Empty environment with nighttime idle lighting.",
            duration_s=120,
        ),

        "one_pedestrian": Scenario(
            name="one_pedestrian",
            description="A pedestrian triggers path lamps in sequence.",
            duration_s=120,
            agents=(pedestrian(),),
        ),

        "repeated_movement": Scenario(
            name="repeated_movement",
            description="Two pedestrians extend nearby lamps' hold periods.",
            duration_s=120,
            agents=(
                pedestrian("PERSON_1", 5.0),
                pedestrian("PERSON_2", 25.0),
            ),
        ),

        "animal_edge": Scenario(
            name="animal_edge",
            description=(
                "An animal moves along the habitat edge and triggers E1. "
                "Detection does not use its species or agent type."
            ),
            duration_s=120,
            agents=(
                Agent(
                    agent_id="ANIMAL_1",
                    agent_type="animal",
                    route=((0.0, 20.0), (60.0, 20.0)),
                    speed_m_s=0.8,
                    start_time_s=5.0,
                ),
            ),
        ),

        "day_night_cycle": Scenario(
            name="day_night_cycle",
            description="Daytime, then nighttime, then daytime again.",
            duration_s=120,
            agents=(pedestrian(start_time_s=25.0),),
            night_windows=((20, 90),),
        ),

        "sensor_fault": Scenario(
            name="sensor_fault",
            description="P1's sensor fails and then recovers on an empty path.",
            duration_s=120,
            fault_windows=(("P1", 40, 45),),
        ),

        "stale_sensor": Scenario(
            name="stale_sensor",
            description="P1 stops receiving fresh samples, then recovers.",
            duration_s=120,
            stale_windows=(("P1", 4, 10),),
        ),
    }


def get_scenario(name):
    scenarios = get_scenarios()

    if name not in scenarios:
        raise ValueError(
            f"Unknown scenario: {name}. "
            f"Choose from: {', '.join(scenarios)}"
        )

    return scenarios[name]


def main():
    for scenario in get_scenarios().values():
        print(
            f"{scenario.name}: {scenario.duration_s}s, "
            f"{len(scenario.agents)} agent(s)"
        )
        print(f"  {scenario.description}")


if __name__ == "__main__":
    main()