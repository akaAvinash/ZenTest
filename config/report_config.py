import os
from datetime import datetime

REPORT_BASE_DIRECTORY = "reports"

def generate_report() -> str:
    """
    Builds a unique report with timestamp.
    File path - /reports/filename
    Report sample format - zentest_report_20260829_161530
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(REPORT_BASE_DIRECTORY, f"zentest_report_{timestamp}")
