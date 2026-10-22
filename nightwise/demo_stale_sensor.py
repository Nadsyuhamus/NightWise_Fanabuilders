"""Demonstrate missing updates, stale detection and recovery."""

from simulation import Simulation


def main():
    simulation = Simulation(agents=[])

    print("SIMULATED STALE SENSOR — P1")
    print("Time | Sample age | Status  | Brightness | Mode")

    for time_s in range(12):
        # Last fresh sample before interruption arrives at 3s.
        # Fresh samples resume at 10s.
        blocked = {"P1"} if 4 <= time_s < 10 else set()

        frame = simulation.step(
            time_s=time_s,
            stale_lamp_ids=blocked,
        )

        lamp = next(
            item
            for item in frame["lamps"]
            if item["lamp_id"] == "P1"
        )

        age = lamp["sample_age_s"]
        age_text = "missing" if age is None else f"{age:.0f}s"

        print(
            f"{time_s:>4}s | "
            f"{age_text:>10} | "
            f"{lamp['sensor_status']:<7} | "
            f"{lamp['brightness_pct']:>9.1f}% | "
            f"{lamp['mode']}"
        )


if __name__ == "__main__":
    main()