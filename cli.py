import argparse
import os
import subprocess
import sys
from utils.config import generate_report
from utils.logger import get_logger

# Maps a "module" name to its test folder.
MODULE_MAP = {
    "ui_test": "tests/ui_tests/tests",
    "api_test": "tests/api_tests/tests",
    "db_test": "tests/db_tests/tests",
}

def build_pytest_args(module: str, smoke: bool) -> list[str]:
    folder = MODULE_MAP[module]
    args = [folder]
    if smoke:
        args += ["-m", "smoke"]
    return args

def list_tests(module: str, smoke: bool):
    logger = get_logger(__name__)
    args = ["pytest", "--collect-only", "-q"] + build_pytest_args(module, smoke)
    logger.debug("Listing %s tests (smoke=%s): %s", module, smoke, " ".join(args))
    result = subprocess.run(args)
    sys.exit(result.returncode)

def run_tests(module: str, smoke: bool):
    report_dir = generate_report(module)
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/zentest_report.html"
    junit_path = f"{report_dir}/junit.xml"
    artifacts_dir = f"{report_dir}/artifacts"

    # Route this run's logs (this process and the pytest subprocess it
    # spawns below) into the report folder itself, so zentest.log ships
    # alongside zentest_report.html for every run.
    os.environ["ZENTEST_LOG_DIR"] = report_dir
    logger = get_logger(__name__, log_dir=report_dir)

    args = [
           "pytest",
           f"--html={report_path}",
           "--self-contained-html",
           f"--junitxml={junit_path}",  # feeds Jenkins' native junit step for the test-trend dashboard
           "--screenshot=only-on-failure",
           "--video=retain-on-failure",
           f"--output={artifacts_dir}",  # pytest-playwright: where screenshots/videos land
       ] + build_pytest_args(module, smoke)

    logger.info("Starting %s run (smoke=%s): %s", module, smoke, " ".join(args))
    result = subprocess.run(args)

    if result.returncode != 0 and not os.path.exists(report_path):
        logger.error("pytest failed before a report could be generated (exit code %s)", result.returncode)
        print(f"\npytest failed before a report could be generated (exit code {result.returncode}).")
    elif result.returncode != 0:
        logger.warning("Run finished with failures (exit code %s). Report: %s", result.returncode, report_path)
        print(f"\nReport: {report_path}")
    else:
        logger.info("Run finished successfully. Report: %s", report_path)
        print(f"\nReport: {report_path}")

    # Propagate pytest's exit code — without this, cli.py always exits 0
    # regardless of test outcome, and CI would report every run as green
    # no matter how many tests actually failed.
    sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="ZenTest CLI")
    parser.add_argument("-m", "--module", required=True, choices=MODULE_MAP.keys())
    parser.add_argument("--smoke", action="store_true", help="Filter to smoke-marked tests only")
    parser.add_argument("--start", action="store_true", help="Run tests (default: list only)")
    args = parser.parse_args()

    if args.start:
        run_tests(args.module, args.smoke)
    else:
        list_tests(args.module, args.smoke)


if __name__ == "__main__":
    main()