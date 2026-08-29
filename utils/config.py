import os
from datetime import datetime

# Default to the deployed app for local dev convenience (no server to
# start). CI (or anyone testing a local run) overrides these via env vars
# so tests target the instance actually under test, not production.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://zentest-sael.onrender.com")
API_URL = os.environ.get("API_URL", "https://zentest-sael.onrender.com")

# Where cli.py's HTML reports get written
REPORT_BASE_DIRECTORY = "reports"


def generate_report(module: str = "zentest") -> str:
    """
    Builds a unique report dir path with a timestamp.
    File path - /reports/filename
    Report sample format - api_test_20260829_161530_482913

    Includes microseconds (not just seconds) because two `cli.py --start`
    invocations back-to-back in the same CI pipeline (e.g. API tests then UI
    tests) can both compute their timestamp within the same wall-clock
    second — with second-only precision they'd collide on the same folder
    name and the second run's report/log would silently overwrite the
    first's. The module name is included too so folders stay identifiable
    even in the unlikely event two runs still collide.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return os.path.join(REPORT_BASE_DIRECTORY, f"{module}_{timestamp}")
