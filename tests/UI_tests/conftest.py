import sys
from pathlib import Path

# Make the framework-level utils/ and config/ (repo root) importable from
# inside the test suite too, alongside tests/UI_tests' own pages/utils/config.
# Appended (not inserted first) so tests/UI_tests keeps priority for names
# that exist in both places, e.g. `config` (tests/UI_tests/config.py wins).
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
if str(FRAMEWORK_ROOT) not in sys.path:
    sys.path.append(str(FRAMEWORK_ROOT))

import pytest
from utils.api_helper import clear_cart
from utils.logger import get_logger

logger = get_logger(__name__)
results_logger = get_logger("pytest.results")

@pytest.fixture(autouse=True)
def reset_cart():
    logger.debug("Resetting cart before test")
    clear_cart()
    yield
    logger.debug("Resetting cart after test")
    clear_cart()


def pytest_runtest_logreport(report):
    """Log each test's outcome — and why, on failure — so zentest.log is
    enough to triage a run without opening the HTML report."""
    if report.when != "call":
        return

    if report.outcome == "passed":
        results_logger.info("PASSED: %s (%.2fs)", report.nodeid, report.duration)
    elif report.outcome == "failed":
        results_logger.error(
            "FAILED: %s (%.2fs)\n%s", report.nodeid, report.duration, report.longreprtext
        )
    elif report.outcome == "skipped":
        results_logger.warning("SKIPPED: %s", report.nodeid)