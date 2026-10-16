# NightWise — Environment and Simulation

Owner: Areesha, Person 2

## Purpose

This component provides a fictional township environment, moving agents,
simulated motion sensors, controller integration, estimated power and
artificial illuminance, repeatable scenarios, and matched comparison logs.

All readings and physical estimates are simulated.

## Requirements

- Python 3.10 or newer
- Python standard library only
- Person 1's controller.py and controller_config.json in the same folder

Run commands from the project folder.

## Files

| File | Purpose |
|---|---|
| environment_config.json | Layout, fixture properties and sensor timeout |
| environment.py | Environment configuration loader |
| agents.py | Repeatable agent movement along routes |
| sensors.py | Ideal circular motion detection |
| models.py | Estimated power and artificial illuminance |
| simulation.py | Simulation state and controller integration |
| scenarios.py | Seven repeatable scenario definitions |
| run_simulation.py | Named-scenario runner |
| comparison.py | Matched baseline and NightWise comparison |
| export_results.py | CSV and metadata exports |
| demo_conditions.py | Focused day/night and fault demonstration |
| demo_stale_sensor.py | Focused stale-data demonstration |
| test_simulation.py | Nine simulation tests |

## Environment

The fictional map is 60 m wide by 40 m high.

- Walking path: y = 0 to 15 m
- Habitat edge: y = 15 to 25 m
- Habitat corridor: y = 25 to 40 m

There are three walking-path lamps and one habitat-edge lamp.
No fixture is installed inside the habitat corridor.

Six measurement points estimate artificial illumination on the path
and inside the habitat corridor.

Coordinates and zone assignments are defined in environment_config.json.

## Run Scenarios

List scenarios:

```bash
python scenarios.py
```

Run one scenario:

```bash
python run_simulation.py --scenario one_pedestrian
```

Available scenarios:

- empty_night
- one_pedestrian
- repeated_movement
- animal_edge
- day_night_cycle
- sensor_fault
- stale_sensor

Each scenario lasts 120 simulated seconds with a one-second time step.
No real-time waiting is required.

Time windows include their start and exclude their end.

## Dashboard Integration — Person 3

Use one Simulation instance for a scenario:

```python
from scenarios import get_scenario
from simulation import Simulation

scenario = get_scenario("one_pedestrian")
simulation = Simulation(agents=scenario.agents)

frame = simulation.step(
    time_s=0,
    **scenario.conditions_at(0),
)
```

Each frame contains:

- data_source
- time_s
- agents: active agent IDs, types and coordinates
- lamps: sensor inputs, brightness, mode, reason, sensor status,
  sample age and estimated power
- total_power_w
- lux_readings: measurement-point coordinates and artificial lux

Advance time strictly for each call:

```python
frame = simulation.step(
    time_s=1,
    **scenario.conditions_at(1),
)
```

Reset before replaying:

```python
simulation.reset()
```

The scenario runner additionally supplies scenario and dt_s fields.

For a complete replay:

```python
from run_simulation import run_scenario

simulation, frames = run_scenario("one_pedestrian")
```

Keep the Simulation instance across dashboard updates, such as in
Streamlit session state. Recreate or reset it when restarting a scenario.
Do not advance simulation time merely because the page rerenders.

## Sensor Behaviour

Sensors detect active moving agents within a circular range.
The range boundary is included.

Agent type is used for display only. Detection does not distinguish
people from animals.

Current agents move continuously while active and leave when their
routes finish. Stationary-agent detection is not implemented.

Explicit faults immediately mark the sensor unhealthy.

During a sample interruption, the latest motion sample is cached.
It becomes unhealthy when its age exceeds the configured timeout.
A sensor with no sample is unhealthy immediately.

Day/night is supplied by the scenario, independently of lamp output.
The controller continues receiving updates during sensor failures.

## Physical Assumptions

Default fixture properties:

- Rated power: 40 W
- Height: 4 m
- Full-output illuminance directly below fixture: 20 lux
- Habitat spill multiplier: 0.15

Estimated power:

power_w = rated_power_w × brightness_pct / 100

Estimated artificial illuminance at a measurement point:

lux = sum of each lamp's contribution

Each contribution is:

full_output_lux_below
× brightness_pct / 100
× height_m² / (height_m² + horizontal_distance_m²)
× directional_factor

The directional factor is habitat_spill_factor for habitat-edge and
habitat-corridor measurement points, and 1 elsewhere.

This is a simplified attenuation model, not calibrated photometry.
An unlit habitat corridor can still receive spill from nearby lamps.

Standby, sensor and communication power are excluded.
Ambient daylight and other light sources are excluded from lux estimates.
Spectrum and species-specific effects are not modelled.

## Matched Comparison

Run:

```bash
python comparison.py
```

The fixed baseline uses each zone's configured brightness cap at night:

- Walking path: 70%
- Habitat edge: 30%
- Habitat corridor: 0%

The baseline is off during scheduled daytime and does not depend on
motion sensors.

Both policies share the same agents, timestamps, sensor inputs,
fixtures and shielding.

NightWise uses Person 1's controller. Its fault fallback takes priority
over daytime, so daytime sensor faults may consume power.

This comparison isolates adaptive brightness with unchanged fixtures
and shielding.

## Export Results — Persons 3 and 4

Export one scenario:

```bash
python export_results.py --scenario one_pedestrian
```

Export all scenarios:

```bash
python export_results.py --scenario all
```

Each scenario receives a folder inside outputs/ containing:

| File | Contents |
|---|---|
| sensor_inputs.csv | Shared sensor inputs and health |
| agent_positions.csv | Active agent positions |
| lamp_outputs.csv | Both policies' decisions, watts and interval kWh |
| lux_readings.csv | Both policies' point lux and interval lux-seconds |
| run_metadata.json | Configuration, scenario, assumptions and row counts |

Agent rows exist only while agents are active.
Empty scenarios have a header-only agent_positions.csv.

Re-exporting a scenario overwrites its existing result files.

## Interval Accounting — Person 4

Each row describes the interval:

[time_s, time_s + dt_s)

A 120-second run contains 120 one-second intervals, from [0, 1)
through [119, 120).

Interval energy:

interval_energy_kwh = power_w × dt_s / 3,600,000

Sum interval_energy_kwh across lamps and intervals for each policy.

Interval light exposure:

interval_exposure_lux_s = artificial_lux × dt_s

Sum exposure over time separately for each measurement point.
Divide by total duration to obtain time-averaged lux at that point.

Spatial averages or maxima must be explicitly defined.
Lux-seconds are an illumination-exposure quantity, not energy.

## Verification

Run all tests:

```bash
python -m unittest -v
```

Expected result: 22 passing tests
(13 controller tests and 9 simulation tests).

Save results:

```bash
python -m unittest -v > simulation_test_results.txt 2>&1
```

Checks cover agent movement, sensor boundaries, power and energy units,
light contributions, independent lamps, daylight, fault recovery,
missing/stale samples, replay consistency and matched scenario inputs.

## Limitations

- Results are illustrative simulations, not measured township performance.
- Short-scenario savings must not be presented as annual predictions.
- Lower habitat lux does not demonstrate wildlife recovery.
- Resident safety and lighting-standard compliance are not established.
- No CCTV, computer vision or AI training is included.
- Resident reports are handled separately by the dashboard component.