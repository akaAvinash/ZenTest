import sys
from pathlib import Path

# This conftest.py lives at the repo root, so pytest already puts the root
# itself on sys.path (letting `utils`, etc. resolve). tests/ui_tests/ still
# needs to be added explicitly: its pages/*.py use bare imports like
# `from pages.base_page import ...`, which only resolve if ui_tests/ itself
# (not just tests/) is on sys.path.
ROOT = Path(__file__).resolve().parent
for _subdir in ("tests/ui_tests", "tests/api_tests"):
    _path = str(ROOT / _subdir)
    if _path not in sys.path:
        sys.path.append(_path)

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