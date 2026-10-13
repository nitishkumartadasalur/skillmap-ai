"""End-to-end UI smoke test using Streamlit's AppTest.

Skipped automatically when Streamlit or Plotly is not installed.
"""

import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
    import plotly  # noqa: F401
except ImportError:  # pragma: no cover
    AppTest = None

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@unittest.skipIf(AppTest is None, "streamlit/plotly not installed")
class AppSmokeTests(unittest.TestCase):
    def test_loads_without_errors(self):
        at = AppTest.from_file(APP, default_timeout=60).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])

    def test_sample_flow_produces_results(self):
        at = AppTest.from_file(APP, default_timeout=60).run()
        at.radio(key="resume_mode").set_value("Use a sample").run()
        at.button(key="btn_load_jobs").click().run()
        at.button(key="btn_analyze").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertTrue(at.get("download_button"), "Export buttons should appear after analysis")


if __name__ == "__main__":
    unittest.main()
