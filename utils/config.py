import os
from datetime import datetime

# Test target URLs — same origin for both, since FastAPI serves the
# frontend and API from a single process. Point both at
# http://127.0.0.1:8000 to test against a local run instead.
FRONTEND_URL = "https://zentest-sael.onrender.com"
API_URL = "https://zentest-sael.onrender.com"

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
