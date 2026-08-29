import os
from datetime import datetime

# Default to the deployed app for local dev convenience (no server to
# start). CI (or anyone testing a local run) overrides these via env vars
# so tests target the instance actually under test, not production.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://zentest-sael.onrender.com")
API_URL = os.environ.get("API_URL", "https://zentest-sael.onrender.com")

# Where cli.py's HTML reports get written
REPORT_BASE_DIRECTORY = "reports"


def generate_report() -> str:
    """
    Builds a unique report dir path with a timestamp.
    File path - /reports/filename
    Report sample format - zentest_report_20260829_161530
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(REPORT_BASE_DIRECTORY, f"zentest_report_{timestamp}")
