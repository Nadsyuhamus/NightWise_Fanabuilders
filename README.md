NightWise - Lighting Controller Starter
Person 1's Python rule-based lighting controller. No trained AI, Node-RED,
Streamlit or external Python packages are needed to run this starter.
Synthetic inputs are used only for rule-based scenario testing.
Start in VS Code
1. Install Python 3.10 or newer and VS Code's Python extension.
2. Open this repository folder in VS Code.
3. Open Terminal > New Terminal. Select your Python interpreter if prompted.
4. Run python demo_controller.py (on macOS, use python3 if needed).
5. Run python -m unittest -v to check behaviour.
Files
- controller.py: zone profiles, input/output definitions and controller state.
- demo_controller.py: small repeatable scenario; temporary stand-in for Person 2.
- test_controller.py: behaviour checks.
Proposed contract to agree with Person 2
Input per lamp: lamp_id, zone, time_s, motion, is_night, sensor_ok.
Zone IDs: walking_path, habitat_edge, habitat_corridor.
Time is simulation seconds, strictly increasing per lamp. Call reset() before replay.
Output: lamp_id, zone, brightness_pct, mode, reason.
Use dataclasses.asdict(result) if a dictionary is needed.
Person 2 creates agents, sensor signals and the environment's light/power model.
This controller never receives agent identity or species labels. It only decides
brightness. Person 3 renders the world and Person 4 calculates impact from logs.
Person 2 must flag stale/missing required data with sensor_ok=False.
Illustrative settings - NOT deployment standards
Zone	Idle	Movement/hold	Fault fallback
Walking path	30%	70%	50%
Habitat edge	10%	30%	20%
Habitat corridor	0%	0%	0%


Movement refreshes a 30-second hold. Brightening is immediate; dimming proceeds
at 10 percentage points per second after hold expiry. No movement-based species
recognition is claimed. Fault handling takes precedence over daylight handling.
The unlit habitat corridor is not a pedestrian route.
Real lighting targets, safety, stale-data timing, shielding and hardware controls
require later design review. Brightness is not a lux measurement or a power
measurement. The demo reports decisions only, not measured environmental savings.
First exercises
1. Run the demo and explain every line.
2. Change the demo zone to habitat_edge and compare the output.
3. Add a second movement event and observe the extended hold.
4. Agree this contract with Person 2 before adding integration features.