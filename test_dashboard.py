"""Regression checks for energy values actually rendered by the dashboard."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from comparison import run_comparison
from impact import compare_energy, format_reduction_pct
from scenarios import get_scenarios


class DashboardTests(unittest.TestCase):
    def test_displayed_energy_matches_shared_calculations(self):
        app = AppTest.from_file(
            str(Path(__file__).with_name("app.py")), default_timeout=30
        ).run()
        self.assertEqual(len(app.exception), 0)

        for name in get_scenarios():
            with self.subTest(scenario=name):
                app.selectbox(key="scenario_name").select(name).run()
                self.assertEqual(len(app.exception), 0)

                comparison = run_comparison(name)
                expected = compare_energy(
                    comparison["nightwise"], comparison["fixed_baseline"]
                )
                # KPIs use custom HTML, so inspect rendered Markdown,
                # rather than app.metric (which would find no KPIs).
                rendered = "\n".join(item.value for item in app.markdown)
                values = {
                    "Energy reduction": format_reduction_pct(expected["savings_pct"]),
                    "Energy difference": f"{expected['saved_kwh'] * 1000:+.4f} Wh",
                    "Smart lamps used": f"{expected['adaptive_kwh'] * 1000:.2f} Wh",
                    "Fixed baseline": f"{expected['baseline_kwh'] * 1000:.2f} Wh",
                }
                for label, value in values.items():
                    self.assertIn(
                        f'<div class="kpi-label">{label}</div>'
                        f'<div class="kpi-value">{value}</div>',
                        rendered,
                        msg=f"{name}: incorrect displayed {label}",
                    )


if __name__ == "__main__":
    unittest.main()
