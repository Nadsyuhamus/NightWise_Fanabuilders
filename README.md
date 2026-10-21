# NightWise: Lighting That Protects Nature

NightWise is a township lighting prototype that aims to reduce unnecessary
nighttime lighting and light spill while maintaining appropriate visibility
on pedestrian paths.

The project combines:
- A simulated township environment with moving agents
- Simulated movement and lighting sensors
- A rule-based Python lighting controller
- A Streamlit dashboard
- Manual resident feedback and wildlife reports
- Estimated energy and light-exposure comparisons

Synthetic data is used for rule-based scenario testing only, not AI training.

## Current Implementation

This folder currently contains the lighting controller, configuration,
standalone demonstration, and automated tests.

The controller:
- Applies different lighting rules to three zones
- Brightens lamps when movement is detected
- Holds brightness after the latest movement
- Gradually dims lamps after the hold expires
- Enforces zone-specific brightness caps
- Uses zone-specific fallback settings when sensor data is unusable
- Turns lamps off during daytime when sensor inputs are healthy
- Returns a decision reason for dashboard display

The simulation environment, dashboard, and impact calculations are separate
components to be integrated by the team.

No CCTV or automatic wildlife recognition is included in the current version.
Wildlife sightings will be reported manually by residents.

## Requirements

- Python 3.10 or newer
- VS Code is recommended
- No external Python packages are required for the controller

All imports use Python's standard library.

## Files

| File | Purpose |
|---|---|
| `controller.py` | Input validation, lamp state, and lighting decisions |
| `controller_config.json` | Zone brightness settings and controller timing |
| `demo_controller.py` | Five synthetic scenarios across three zones |
| `test_controller.py` | Thirteen automated controller tests |
| `README.md` | Setup, behaviour, and integration documentation |

Generated after running the relevant commands:

| File | Purpose |
|---|---|
| `controller_demo_log.csv` | Scenario inputs and controller decisions |
| `controller_test_results.txt` | Saved automated test output |

## Setup in VS Code

1. Clone the repository:

```bash
git clone https://github.com/Nadsyuhamus/NightWise_NeoFantic.git
cd NightWise_NeoFantic
```

2. Open the repository folder in VS Code.

3. Install the Python extension by Microsoft.

4. Select a Python 3.10 or newer interpreter.

5. Open Terminal → New Terminal.

Check your Python version:

```bash
python3 --version
```

On systems that use `python` instead of `python3`, substitute that command
throughout these instructions.

## Run the Controller Demonstration

```bash
python3 demo_controller.py
```

The demonstration prints:
- Scenario name
- Simulation time
- Zone
- Brightness percentage
- Operating mode
- Decision reason

It runs five scenarios:

1. Empty area
2. Movement, hold period, and gradual fading
3. Repeated movement extending the hold
4. Sensor failure and recovery
5. Daytime-to-nighttime transition

Each scenario runs across:
- Walking path
- Habitat edge
- Habitat corridor

The demonstration exports 51 decisions to:

```text
controller_demo_log.csv
```

Simulation timestamps do not require waiting in real time.

Running `controller.py` alone does not print a demonstration. It defines the
classes used by the demo and future integration.

## Run the Tests

```bash
python3 -m unittest -v
```

Expected summary:

```text
Ran 13 tests
OK
```

The tests cover:

1. Empty-area operation
2. Hold duration and gradual fading
3. Irregular update intervals
4. Repeated movement
5. Sensor faults and recovery
6. Daytime-to-nighttime transition
7. Fault handling taking priority over daytime
8. Habitat-edge and habitat-corridor settings
9. Independent lamp states
10. Timestamp validation and scenario reset
11. Invalid sensor inputs
12. Preventing zone changes during a run
13. Custom timing and configuration validation

Save test output for the project handoff:

```bash
python3 -m unittest -v > controller_test_results.txt 2>&1
```

## Controller Configuration

Settings are loaded from `controller_config.json`, located beside
`controller.py`.

### Default Zone Settings

| Zone ID | Idle | Occupied / hold | Fault fallback | Maximum cap |
|---|---:|---:|---:|---:|
| `walking_path` | 30% | 70% | 50% | 70% |
| `habitat_edge` | 10% | 30% | 20% | 30% |
| `habitat_corridor` | 0% | 0% | 0% | 0% |

These are illustrative simulation settings, not approved real-world
lighting standards.

The habitat corridor represents an unlit natural area, not a pedestrian route.

### Default Timing

| Parameter | Value | Meaning |
|---|---:|---|
| `hold_seconds` | 30 | Hold occupied brightness after the latest movement |
| `fade_pct_per_second` | 10 | Reduce brightness by 10 percentage points per second after hold expiry |

Brightening is immediate when movement is detected.

At the exact hold-expiry timestamp, the lamp remains at occupied brightness.
Fading applies to elapsed time after that boundary.

For example, movement at 1 second holds the walking-path lamp at 70% through
31 seconds. At 32 seconds, it fades to 60%.

### Configuration Rules

The controller validates that:
- All three supported zones are present
- Brightness values are finite numbers between 0 and 100
- `idle <= occupied <= cap`
- `fallback <= cap`
- Every habitat-corridor brightness setting is zero
- Hold duration is finite and nonnegative
- Fade rate is finite and positive

Edit the JSON settings before creating a controller instance. An existing
instance does not automatically reload configuration changes.

## Proposed Input Contract

Person 2's environment supplies one `SensorInput` per lamp.

```python
from controller import SensorInput

reading = SensorInput(
    lamp_id="P1",
    zone="walking_path",
    time_s=0.0,
    motion=False,
    is_night=True,
    sensor_ok=True,
)
```

| Field | Type | Meaning |
|---|---|---|
| `lamp_id` | `str` | Nonempty unique lamp identifier |
| `zone` | `str` | One of the three supported zone IDs |
| `time_s` | `float` | Elapsed simulation time in seconds; integers are also accepted |
| `motion` | `bool` | Whether movement is detected |
| `is_night` | `bool` | Whether nighttime lighting rules apply |
| `sensor_ok` | `bool` | Whether required sensor inputs are usable |

### Input Requirements

- Time must be finite and nonnegative.
- Time must strictly increase for each lamp.
- Different lamps may share the same timestamp.
- A lamp's zone must remain fixed during a run.
- Sensor flags must be actual booleans, not strings or integers.
- Call `reset()` before replaying a scenario from time zero.

The environment must set `sensor_ok=False` when required sensor data is
missing, faulty, or stale. The controller does not independently detect
staleness or run a timeout when updates stop arriving.

The environment determines `is_night`. The current controller does not
derive it from a lux measurement.

The controller receives movement signals, not agent identities or species
labels. It does not distinguish people from wildlife.

## Output Contract

```python
from dataclasses import asdict
from controller import LightingController, SensorInput

controller = LightingController()

reading = SensorInput(
    lamp_id="P1",
    zone="walking_path",
    time_s=0.0,
    motion=False,
    is_night=True,
    sensor_ok=True,
)

decision = controller.update(reading)

print(asdict(decision))
```

Example output:

```python
{
    "lamp_id": "P1",
    "zone": "walking_path",
    "brightness_pct": 30.0,
    "mode": "idle",
    "reason": "No recent motion",
}
```

| Field | Meaning |
|---|---|
| `lamp_id` | Lamp receiving the decision |
| `zone` | Lamp's configured zone |
| `brightness_pct` | Requested brightness, rounded to two decimal places |
| `mode` | Current operating mode |
| `reason` | Human-readable explanation |

### Operating Modes

| Mode | Meaning |
|---|---|
| `idle` | Lamp has reached the zone's idle brightness |
| `occupied` | Movement was detected or the hold period is active |
| `fading` | Lamp is gradually returning to idle brightness |
| `fallback` | Required sensor inputs are unusable |
| `daylight` | Lamp is off during daytime |
| `protected` | Habitat corridor remains unlit at night |

## Rule Priority

The controller applies rules in this order:

1. Scheduled daytime → lamp off, regardless of motion-sensor health
2. Nighttime motion-sensor fault or unavailable sample → zone-specific fallback
3. Healthy nighttime habitat corridor → remain unlit
4. Movement or active hold → occupied brightness
5. Otherwise → gradually return to idle brightness

All outputs are bounded by the zone's brightness cap.

The simulation assumes its day/night schedule is trustworthy and
independent of motion-sensor health. Daytime motion faults remain
reported but do not activate lighting. A fault that persists into
nighttime activates the configured fallback.

Daytime and fault operation clear the previous movement history.

After fault recovery:
- New movement immediately restores occupied brightness.
- Without movement, brightness returns toward idle at the configured fade rate.

After daytime ends, the lamp immediately restores at least idle brightness
on its next healthy nighttime update.

## Simulation Integration

Use one controller instance throughout a scenario:

```python
from dataclasses import asdict
from controller import LightingController, SensorInput

controller = LightingController()

events = [
    SensorInput("P1", "walking_path", 0, False, True),
    SensorInput("P1", "walking_path", 1, True, True),
    SensorInput("P1", "walking_path", 32, False, True),
]

for reading in events:
    decision = controller.update(reading)
    print(asdict(decision))
```

Before replaying:

```python
controller.reset()
```

The intended system flow is:

1. Simulated agents move through the environment.
2. Simulated sensors generate inputs.
3. The controller returns lamp brightness decisions.
4. The environment applies those decisions to its lamp models.
5. The environment calculates modelled lux and power.
6. The dashboard displays the results.
7. Impact calculations compare matched baseline and adaptive runs.

Do not create a new controller for every update, because that would erase
the movement history needed for holding and fading.

## Team Responsibilities

| Person | Responsibility |
|---|---|
| Nadsyuha | Lighting rules, configuration, controller tests, and control demonstration |
| Areesha | Environment, agents, sensors, power/lux models, and scenario logs |
| Asyura | Dashboard, integration, lighting feedback, and manual wildlife reports |
| Faqihah | Impact calculations, pitch deck, and demo video |

## Decision Log

`controller_demo_log.csv` contains:
- Scenario name
- Synthetic-data label
- Lamp ID and zone
- Simulation timestamp
- Movement, nighttime, and sensor-health inputs
- Brightness, mode, and decision reason

This is a controller decision log, not a measured energy dataset.

It does not contain power or lux measurements. Person 2 must provide the
environment's power/lux model and appropriate sampling logs before Person 4
calculates environmental comparisons.

## Limitations and Future Work

- Brightness percentage is not a lux value or power measurement.
- Current habitat constraints limit brightness; they do not enforce a
  habitat-side lux threshold.
- Shielding, spectrum, fixture geometry, and light spill require separate
  modelling or physical design.
- Movement sensing does not identify species or reliably detect stationary people.
- Simulated outcomes must be labelled in the dashboard, slides, and video.
- The prototype does not prove resident safety, biodiversity recovery,
  or improved night-sky quality.
- Real deployment requires reviewed lighting targets, fallback behaviour,
  sensor placement, and compatible hardware.
- Manual resident reports enter operator review and do not directly control lamps.
- CCTV and computer vision for resident safety are possible future features.
- Any future AI training must use suitable real data and address privacy.

The next integration step is agreeing on sensor fields, timing, and
missing-data handling with Person 2.