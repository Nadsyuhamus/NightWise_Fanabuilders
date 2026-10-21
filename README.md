# NightWise: Lighting That Protects Nature

NightWise is a township lighting simulation prototype designed to reduce unnecessary nighttime lighting and light spill while supporting visibility on pedestrian paths.

The system combines:

- A simulated township environment with moving agents
- Simulated movement sensors
- A rule-based lighting controller
- Illustrative electrical power and illuminance models
- A Streamlit dashboard
- Manual wildlife sightings and lighting feedback
- Matched fixed-versus-adaptive lighting comparisons

Synthetic data is used for scenario testing, not AI training.

## Current Implementation

The simulation generates movement and sensor inputs. The controller uses these inputs to adjust each lamp’s brightness according to its zone, recent movement, day/night schedule, and sensor health.

The system then estimates power consumption and illuminance. The dashboard displays the simulation, controller decisions, and impact comparisons.

Community reports provide information for operator attention. They do not directly control lamps.

This prototype does not connect to physical sensors or lighting hardware. It does not include CCTV, automatic wildlife recognition, or a trained AI model.

## Lighting Behaviour

The controller supports three zones:

| Zone | Idle brightness | Movement/hold brightness | Nighttime fault fallback | Maximum brightness |
|---|---:|---:|---:|---:|
| Walking path | 30% | 70% | 50% | 70% |
| Habitat edge | 10% | 30% | 20% | 30% |
| Habitat corridor | 0% | 0% | 0% | 0% |

Default behaviour:

- Movement immediately increases brightness to the zone’s occupied setting.
- Brightness remains elevated for 30 seconds after the latest detection.
- After the hold period, brightness decreases by 10 percentage points per second until it reaches the idle setting.
- Scheduled daytime turns lamps off.
- Unusable nighttime motion inputs activate the zone’s fallback setting.
- The habitat corridor has no direct lighting, although nearby lamps may contribute modelled light spill.

These settings are illustrative simulation parameters, not approved lighting standards. The controller does not distinguish people from wildlife.

## Requirements

- Python 3.10 or newer
- Streamlit, Plotly, and pandas for the dashboard
- A writable local directory if SQLite report storage is enabled

The controller uses Python’s standard library. The dashboard requires external packages.

## Setup

Clone the repository:

```bash
git clone https://github.com/QihahFirhat/NightWise_NeoFantic.git
cd NightWise_NeoFantic
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies if `requirements.txt` is available:

```bash
python -m pip install -r requirements.txt
```

Otherwise, install the dashboard packages directly:

```bash
python -m pip install streamlit plotly pandas
```

The examples below use `python`. Use `python3` instead if required by your system.

## Run the Dashboard

```bash
python -m streamlit run app.py
```

Open the local address printed in the terminal.

The dashboard provides:

- A live simulated environment
- Lamp brightness and operating states
- Movement and sensor information
- Energy and habitat-lighting comparisons
- Wildlife sighting and lighting feedback forms

All simulation outputs should be interpreted as modelled estimates.

## Run the Controller Demonstration

```bash
python demo_controller.py
```

The demonstration prints:

- Scenario name
- Simulation time
- Zone
- Brightness percentage
- Operating mode
- Decision reason

It covers:

1. Empty-area operation
2. Movement, holding, and gradual fading
3. Repeated movement extending the hold
4. Sensor failure and recovery
5. Daytime-to-nighttime transition

The scenarios demonstrate behaviour across the walking path, habitat edge, and habitat corridor.

Controller decisions are exported to:

```text
controller_demo_log.csv
```

Simulation timestamps do not require waiting in real time.

Running `controller.py` directly does not start the demonstration or dashboard. It defines the controller classes used by other components.

## Run Automated Checks

Run the project tests:

```bash
python -m unittest discover -v
```

A successful run ends with:

```text
OK
```

Save the test output if needed:

```bash
python -m unittest discover -v > test_results.txt 2>&1
```

The tests cover controller behaviour, simulation behaviour, and impact calculations. Test counts may change as the project develops.

## Main Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit dashboard and community submission forms |
| `controller.py` | Lighting decisions, input validation, and lamp state |
| `controller_config.json` | Zone brightness settings and controller timing |
| `demo_controller.py` | Standalone controller demonstration |
| `environment.py` | Environment loading and configuration support |
| `environment_config.json` | Simulated environment configuration |
| `agents.py` | Simulated moving agents |
| `sensors.py` | Simulated sensor behaviour |
| `models.py` | Illustrative power and illuminance models |
| `simulation.py` | Simulation execution |
| `scenarios.py` | Named scenario definitions |
| `comparison.py` | Matched fixed/adaptive comparisons |
| `impact.py` | Shared impact calculations |
| `export_results.py` | Results export |
| `test_controller.py` | Controller tests |
| `test_simulation.py` | Simulation tests |
| `test_impact.py` | Impact calculation tests |
| `SIMULATION_README.md` | Additional simulation documentation |

The optional report-storage update adds `report_store.py` for SQLite persistence.

## Energy and Light-Exposure Comparisons

Fixed and adaptive lighting must be compared over the same scenario, duration, environment, and sampling intervals. The fixed-lighting policy must be stated alongside the results.

Energy is calculated from power over time:

```text
Energy (kWh) = Σ[Power (W) × Interval duration (s)] / 3,600,000
```

Energy savings are calculated as:

```text
Savings (%) = (Fixed energy − Adaptive energy) / Fixed energy × 100
```

If fixed energy is zero, percentage savings are undefined and should be reported as `N/A`. Negative savings indicate that adaptive operation consumed more energy.

Habitat summaries describe modelled artificial illuminance and exposure at the configured sampling locations. Results should identify the locations and whether the summary covers nighttime only or the full run.

## Community Reports

Residents can submit:

- Wildlife sightings, including species, zone, and an optional note
- Lighting feedback identifying an area as too dark or too bright

A submission does not mean an operator has reviewed it. Reports should be labelled **Pending review** unless an actual review action has been recorded.

### Storage

The original dashboard stores reports in Streamlit session state. These entries are temporary and are not durable records.

If the SQLite report-storage update has been installed and connected to `app.py`, submissions are saved to:

```text
data/community_reports.sqlite3
```

That update gives each submission:

- A unique report ID
- A UTC timestamp
- A `Pending review` status

SQLite records survive browser sessions and local app restarts while the database file remains available. Hosted deployments require persistent storage to retain records across redeployments.

Exclude the database from Git. The prototype does not yet include operator authentication, review actions, or a review audit trail.

## Configuration

Edit `controller_config.json` to adjust zone brightness settings, hold duration, and fade rate.

Edit `environment_config.json` to adjust the simulated environment.

Configuration changes affect the simulation assumptions and may change comparison results. Rerun the relevant tests and regenerate results after making changes.

Brightness percentage is not a direct measurement of electrical power or illuminance. Those quantities depend on the models and their assumptions.

## Limitations

- Results are simulated estimates, not physical measurements.
- Brightness settings have not been validated against real pedestrian-lighting requirements.
- Movement sensing does not identify species or guarantee detection of stationary people.
- No direct lighting inside the habitat corridor does not guarantee zero light spill.
- Power and illuminance models simplify real fixture behaviour.
- Habitat exposure summaries do not demonstrate ecological recovery.
- The prototype does not prove improved resident safety or night-sky quality.
- Expected real-world benefits must be distinguished from demonstrated simulation results.
- Real deployment requires validated lighting targets, suitable hardware, sensor placement, and reviewed fault behaviour.