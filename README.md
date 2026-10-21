# NightWise: Lighting That Protects Nature

NightWise is a township lighting simulation prototype that explores how movement-responsive lighting could reduce unnecessary nighttime electricity use and artificial light reaching nearby habitat while supporting visibility on pedestrian paths.

The prototype combines a simulated environment, moving agents, simulated sensors, a rule-based controller, illustrative power and illuminance models, and a Streamlit dashboard. It also supports manual wildlife sightings, lighting feedback, and matched fixed-versus-adaptive lighting comparisons.

**All energy, illuminance, and exposure results are simulated estimates. Pedestrian safety, ecological recovery, and improved night-sky quality have not been demonstrated.** Synthetic data is used for scenario testing, not AI training.

## How It Works

1. Moving agents generate simulated movement and sensor inputs.
2. The controller determines lamp brightness using zone settings, recent movement, the day/night schedule, and input health.
3. The simulation estimates lamp power and artificial illuminance.
4. The dashboard displays movement, lamp states, controller decisions, and impact comparisons.
5. Community reports provide information for operator attention; they do not directly control lamps.

The prototype does not connect to physical sensors or lighting hardware. It does not include CCTV, automatic wildlife recognition, or a trained AI model. Movement sensing does not distinguish people from wildlife.

## Lighting Behaviour

Default zone settings are:

| Zone | Idle brightness | Movement/hold brightness | Nighttime motion-input fallback | Maximum brightness |
|---|---:|---:|---:|---:|
| Walking path | 30% | 70% | 50% | 70% |
| Habitat edge | 10% | 30% | 20% | 30% |
| Habitat corridor | 0% | 0% | 0% | 0% |

- Movement immediately raises brightness to the zone's occupied setting.
- Brightness remains elevated for 30 seconds after the latest detection. Repeated detections extend the hold period.
- After the hold period, brightness decreases by 10 percentage points per second until it reaches the idle setting.
- With usable day/night information, scheduled daytime turns lamps off.
- Unusable nighttime motion inputs activate the configured zone fallback while the controller continues running.
- The habitat corridor has no direct lighting, but nearby lamps may still contribute modelled light spill.

These values are illustrative simulation parameters, not approved lighting standards. The nighttime motion-input fallback values above do not define every input-failure case; day/night-input failures must be checked separately against the controller policy.

## Requirements

- Python 3.10 or newer
- Streamlit, Plotly, and pandas for the dashboard
- A writable local directory when SQLite report storage is enabled

The controller uses Python's standard library. The dashboard requires external packages.

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

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

If your checkout does not include `requirements.txt`, install the dashboard packages directly:

```bash
python -m pip install streamlit plotly pandas
```

The commands use `python`; use `python3` instead if required by your system.

## Run the Dashboard

```bash
python -m streamlit run app.py
```

Open the local address printed in the terminal. The dashboard provides the simulated environment, lamp brightness and operating states, movement and sensor information, energy and habitat-lighting comparisons, and community submission forms.

## Run the Controller Demonstration

```bash
python demo_controller.py
```

The demonstration prints the scenario, simulation time, zone, brightness, operating mode, and decision reason. It covers:

1. Empty-area operation
2. Movement, holding, and gradual fading
3. Repeated movement extending the hold
4. Sensor failure and recovery
5. Daytime-to-nighttime transition

The scenarios demonstrate behaviour across the walking path, habitat edge, and habitat corridor. Controller decisions are exported to `controller_demo_log.csv`.

Simulation timestamps do not require waiting in real time. Running `controller.py` directly does not launch the dashboard or demonstration; it defines the controller classes used by other components.

## Run Automated Checks

```bash
python -m unittest discover -v
```

A successful run ends with `OK`. Save the output when preparing a test log:

```bash
python -m unittest discover -v > test_results.txt 2>&1
```

The test suite covers controller behaviour, simulation behaviour, and impact calculations. Test counts may change as the project develops. A passing suite verifies the cases it exercises; it does not establish hardware reliability, lighting-standard compliance, or ecological outcomes.

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

The optional SQLite report-storage update adds `report_store.py`.

## Energy and Habitat-Light Exposure

### Fixed Baseline and Fair Comparison

The fixed baseline operates each zone at its configured maximum brightness during scheduled nighttime and switches off during scheduled daytime.

Fixed and adaptive runs use matching fixtures, fixture specifications, shielding, measurement points, controller configuration, agents, sensor inputs, and simulation intervals. Brightness, power, illuminance, and operating modes may differ because they are policy outputs.

Comparison validation rejects mismatched configurations, measurement geometry, inputs, incomplete records, and inconsistent intervals. The named scenario runner also checks the expected scenario start and end times.

Matched conditions support a controlled policy comparison. They do not establish equivalent pedestrian visibility or lighting-standard compliance.

### Calculations

Energy integrates power over each interval:

```text
Energy (kWh) = Σ[Power (W) × Interval duration (s)] / 3,600,000
```

Savings are relative to the declared fixed baseline:

```text
Savings (%) = (Fixed energy − Adaptive energy) / Fixed energy × 100
```

If fixed energy is zero, percentage savings are undefined and must be reported as `N/A`. Retain negative savings: they indicate that adaptive operation consumed more energy. Report the absolute energy difference alongside the percentage.

Habitat summaries describe modelled artificial illuminance at configured sampling locations. Identify the locations, habitat zone, and whether each summary covers nighttime only or the full run. Exposure integrates illuminance over time:

```text
Exposure (lux·h) = Σ[Illuminance (lux) × Interval duration (s)] / 3,600
```

Mean illuminance should use interval-duration weighting when intervals vary. State the units for mean and peak illuminance (`lux`) and exposure (`lux·h`). These metrics describe modelled light conditions; they do not measure biological effects.

### Modelling Assumptions

- Energy represents **modelled lamp-only consumption**. Sensor, controller, networking, and other auxiliary loads are excluded.
- The power model assumes power scales linearly with brightness; real fixture behaviour requires calibration.
- Illuminance and shielding are illustrative model estimates, not calibrated field measurements.
- Brightness percentage is a control setting, not a direct measurement of power or illuminance.
- Reduced habitat-side illuminance or exposure does not establish ecological recovery.

## Community Reports

Residents can submit wildlife sightings, including species, zone, and an optional note, or lighting feedback identifying an area as too dark or too bright.

Submissions provide information for operator attention. A submission does not demonstrate that a report has been reviewed or resolved. Use **Pending review** unless an actual review action has been recorded.

### Storage

Storage depends on the installed implementation:

| Implementation | Retention |
|---|---|
| Original Streamlit session-state storage | Temporary entries; not durable records |
| SQLite update installed and connected to `app.py` | Persistent local records while the database file remains available |

The SQLite update stores reports in:

```text
data/community_reports.sqlite3
```

Each submission receives a unique report ID, a UTC timestamp, and a `Pending review` status. Records survive browser sessions and local app restarts while the database file is retained. Hosted deployments require persistent storage to retain records across redeployments.

Exclude the database from Git. The prototype does not yet include operator authentication, review actions, or a review audit trail.

## Failure Handling and Operational Limits

**Sensor fallback requires the controller to continue running. It does not protect against a total application failure.**

The simulation can evaluate unusable or stale sensor inputs while software execution continues. If the controller process stops, crashes, or loses power, it cannot execute fallback rules or send further commands. The prototype has no demonstrated physical lamp response for that situation.

| Failure | Current boundary |
|---|---|
| Motion input fails while the controller runs | Configured fallback can operate according to the controller's day/night and input-health policy. |
| Sensor updates become stale while the controller runs | Stale-input handling depends on continued controller execution and input-age checks. |
| Dashboard pauses, closes, or becomes unavailable | Interface state does not establish physical lamp behaviour or prove that a separate controller continues running. |
| Controller/application crashes | Software fallback cannot execute; physical lamp behaviour is unverified. |
| Communications fail | No physical communications interface or independently operating lamp fallback has been demonstrated. |
| Electrical power fails | Software cannot maintain illumination without appropriate backup power. |

Do not describe fallback brightness as a validated safe lighting level. Its suitability requires approved lighting targets and physical assessment.

### Manual Recovery Checks

Perform these checks on a disposable test instance and record the actual outcome. They are a verification checklist, not a claim that the checks have passed.

| Check | Procedure | What to record |
|---|---|---|
| Application termination | Start a simulation, then terminate the app process. | Processing stops; this does not demonstrate physical lamp fallback. |
| Restart recovery | Relaunch the application after termination. | Whether startup succeeds and whether the simulation resets or resumes. |
| Report durability | If SQLite storage is enabled, submit a test report, terminate the app, and restart. | Whether the saved report remains available. |
| Interrupted results | Stop a run before its intended end and inspect any retained or exportable results. | Whether the actual duration and incomplete status are clear. |

If interrupted results can be mistaken for a completed run, treat that as an unresolved reporting issue before final integration.

### Future Deployment Requirements

A physical deployment would require:

- An independently running watchdog or local lamp controller that detects missing controller heartbeats.
- An agreed timeout and local lighting policy for communications or controller failure.
- Defined startup, recovery, and power-restoration behaviour.
- Suitable backup power where required by the deployment requirements.
- Physical tests for process crashes, disconnected communications, sensor failures, and power loss.

A dashboard failure toggle can demonstrate a simulated fault scenario. It does not validate protection against an actual controller crash.

## Configuration

Edit `controller_config.json` to adjust zone brightness settings, hold duration, and fade rate. Edit `environment_config.json` to adjust the simulated environment.

Configuration changes alter the simulation assumptions and may change comparison results. Rerun the relevant tests and regenerate results after making changes.

## Results and Integration Handoff

Use one recorded repository revision and configuration for the final dashboard demonstration, exported results, slides, and video.

The final handoff should include:

| Deliverable | Required contents |
|---|---|
| Impact module | Validated energy, savings, and habitat illuminance/exposure calculations |
| Results table | Scenario, actual duration, baseline, energy, savings, habitat summaries, units, and simulated-data label |
| Test log | Commands, environment/dependency versions, outcomes, and unresolved limitations |
| Integration notes | Commit ID, model/configuration versions, scenario settings, interval convention, setup, and team ownership |

Separate software behaviour demonstrated by tests, impact estimated by the simulation, and expected real-world benefits supported by background research. External research does not validate this prototype's numerical results.

## Limitations

- Outputs are simulated estimates, not physical measurements.
- Brightness settings have not been validated against pedestrian-lighting requirements.
- Movement sensing does not identify species or guarantee detection of stationary people.
- No direct lighting inside the habitat corridor does not guarantee zero light spill.
- Power and illuminance models simplify real fixture behaviour.
- Lamp-only energy excludes auxiliary electrical loads.
- Habitat exposure summaries do not demonstrate ecological recovery.
- The prototype does not prove improved resident safety or night-sky quality.
- Sensor fallback depends on continued software execution; total system failure protection is unverified.
- Real deployment requires validated lighting targets, suitable hardware and sensor placement, calibrated models, persistent storage where needed, and reviewed failure/recovery behaviour.
