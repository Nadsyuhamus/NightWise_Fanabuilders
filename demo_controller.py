"""Run: python demo_controller.py. Synthetic inputs for rule-based testing only."""
from controller import LightingController, SensorInput

controller = LightingController()
print("SIMULATED SCENARIO - illustrative settings; no AI training")
print(f"{'Time':>5} {'Brightness':>12} {'Mode':>12}  Reason")
for t, motion, night, healthy in [
    (0, False, True, True), (1, True, True, True),
    (20, False, True, True), (31, False, True, True),
    (32, False, True, True), (35, False, True, True),
    (36, False, True, False), (37, True, True, True),
    (38, False, False, True),
]:
    result = controller.update(SensorInput("L1", "walking_path", t, motion, night, healthy))
    print(f"{t:>5} {result.brightness_pct:>11.0f}% {result.mode:>12}  {result.reason}")
