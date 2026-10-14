# NightWise: Lighting That Protects Nature

NightWise is a township lighting prototype that aims to reduce unnecessary
lighting and light spill while maintaining appropriate visibility on paths.

The project uses a simulated environment and a rule-based lighting controller.
Synthetic data is used for scenario testing only, not AI training.

## Current Component: Lighting Controller

This starter implements Person 1's controller.

It reads sensor inputs and decides lamp brightness based on:

- Zone settings
- Movement detection
- A hold period after movement
- Gradual dimming
- Daytime conditions
- Sensor-fault fallback

The simulation environment, dashboard, impact calculations, and manual
wildlife reporting will be integrated separately.

No CCTV or automatic wildlife recognition is included in this version.

## Requirements

- Python 3.10 or newer
- VS Code is recommended
- No external Python packages are required for this starter

## Files

| File | Purpose |
|---|---|
| `controller.py` | Zone profiles, sensor inputs, decisions, and control logic |
| `demo_controller.py` | Demonstrates one lamp using synthetic sensor inputs |
| `test_controller.py` | Tests controller behaviour |
| `README.md` | Setup instructions and integration contract |

## Run the Demo

Open a terminal inside the project folder:

```bash
python3 demo_controller.py
```

On systems that use `python` instead:

```bash
python demo_controller.py
```

The demo prints simulation timestamps, brightness, operating mode, and
decision reasons. Simulation time does not require waiting in real time.

Running `controller.py` alone does not print a demo; it defines the classes
used by the other files.

## Run the Tests

```bash
python3 -m unittest -v
```

The five tests cover:

- Holding brightness and fading after hold expiry
- Extending the hold when new movement is detected
- Sensor faults, recovery, and daytime operation
- Zone settings and independent lamp states
- Rejecting backward time and resetting a scenario

## Illustrative Zone Settings

| Zone ID | Idle brightness | Movement / hold brightness | Fault fallback |
|---|---:|---:|---:|
| `walking_path` | 30% | 70% | 50% |
| `habitat_edge` | 10% | 30% | 20% |
| `habitat_corridor` | 0% | 0% | 0% |

These values are demonstration settings, not approved real-world lighting
standards. The habitat corridor represents an unlit natural area, not a
pedestrian route.

Default controller timing:

- Hold period: 30 simulation seconds after the latest detected movement
- Fade rate: 10 brightness percentage points per second
- Brightening: immediate when movement is detected
- Dimming: gradual after the hold expires

## Proposed Input Contract

Person 2's simulation supplies one reading per lamp:

```python
from controller import SensorInput

reading = SensorInput(
    lamp_id="L1",
    zone="walking_path",
    time_s=0.0,
    motion=False,
    is_night=True,
    sensor_ok=True,
)
```

| Field | Type | Meaning |
|---|---|---|
| `lamp_id` | `str` | Unique lamp identifier |
| `zone` | `str` | One of the three supported zone IDs |
| `time_s` | `float` | Elapsed simulation time in seconds |
| `motion` | `bool` | Whether the sensor detects movement |
| `is_night` | `bool` | Whether nighttime lighting rules apply |
| `sensor_ok` | `bool` | Whether required sensor inputs are usable |

Time must strictly increase for each lamp. A lamp's zone must remain fixed
during a run. Call `reset()` before replaying from time zero.

The simulation should set `sensor_ok=False` when required sensor data is
missing, faulty, or stale. The controller does not independently detect
staleness.

The controller receives sensor signals, not agent identities or species
labels. Movement sensing does not distinguish people from wildlife.

## Output Contract

```python
from dataclasses import asdict
from controller import LightingController

controller = LightingController()
decision = controller.update(reading)

print(asdict(decision))
```

Example output:

```python
{
    "lamp_id": "L1",
    "zone": "walking_path",
    "brightness_pct": 30,
    "mode": "idle",
    "reason": "No recent motion",
}
```

Supported modes:

| Mode | Meaning |
|---|---|
| `idle` | Lamp is at its zone's idle brightness |
| `occupied` | Movement was detected or the hold period is active |
| `fading` | Lamp is gradually returning to idle brightness |
| `fallback` | Required sensor inputs are not usable |
| `daylight` | Lamp is off during daytime |
| `protected` | Habitat corridor remains unlit |

Sensor-fault handling takes priority over daytime handling. Therefore, a
faulty reading uses the zone's fallback even if `is_night=False`.

## Integration Responsibilities

- **Nadsyuha:** controller rules, decisions, and controller tests
- **Areesha:** environment, moving agents, simulated sensors, and power/lux models
- **Asyura:** dashboard, integration, lighting feedback, and manual wildlife reports
- **Faqihah:** impact calculations, pitch deck, and demo video

## Limitations

- Brightness percentage is not a measured lux value or power reading.
- Simulated outputs must be labelled throughout the dashboard and presentation.
- The controller does not prove resident safety or biodiversity recovery.
- Shielding, light spectrum, and fixture geometry require separate modelling
  or physical design.
- Real deployment requires reviewed lighting targets, fallback settings,
  sensor placement, and compatible hardware.
- Wildlife reports are submitted manually and reviewed by an operator.
- CCTV and computer vision are possible future features, not current functionality.