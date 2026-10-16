"""Demonstrate day/night operation and sensor-fault recovery."""

from simulation import Simulation


def is_night_at(time_s):
    """Illustrative schedule: night from 10s up to, but not including, 70s."""
    return 10 <= time_s < 70


def faulty_lamps_at(time_s):
    """P1's sensor fails from 40s up to, but not including, 45s."""
    return {"P1"} if 40 <= time_s < 45 else set()


def main():
    simulation = Simulation(agents=[])

    snapshot_times = {0, 10, 39, 40, 44, 45, 46, 70}

    print("SIMULATED DAY/NIGHT AND SENSOR FAULT")
    print("Time | Night | Lamp | Healthy | Brightness | Power | Mode")

    for time_s in range(71):
        frame = simulation.step(
            time_s=time_s,
            is_night=is_night_at(time_s),
            faulty_lamp_ids=faulty_lamps_at(time_s),
        )

        if time_s in snapshot_times:
            # Show P1 only to keep this demonstration readable.
            lamp = next(
                item
                for item in frame["lamps"]
                if item["lamp_id"] == "P1"
            )

            print(
                f"{time_s:>4}s | "
                f"{str(lamp['is_night']):<5} | "
                f"{lamp['lamp_id']:<4} | "
                f"{str(lamp['sensor_ok']):<7} | "
                f"{lamp['brightness_pct']:>9.1f}% | "
                f"{lamp['power_w']:>5.1f} W | "
                f"{lamp['mode']}"
            )


if __name__ == "__main__":
    main()