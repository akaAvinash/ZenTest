import argparse
import os
import subprocess
import sys
from config import generate_report

# Maps a "module" name to its test folder.
MODULE_MAP = {
    "ui_test": "tests/UI_tests",
}

def build_pytest_args(module: str, smoke: bool) -> list[str]:
    folder = MODULE_MAP[module]
    args = [folder]
    if smoke:
        args += ["-m", "smoke"]
    return args

def list_tests(module: str, smoke: bool):
    args = ["pytest", "--collect-only", "-q"] + build_pytest_args(module, smoke)
    subprocess.run(args)

def run_tests(module: str, smoke: bool):
    report_dir = generate_report()
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/zentest_report.html"
    artifacts_dir = f"{report_dir}/artifacts"

    args = [
           "pytest",
           f"--html={report_path}",
           "--self-contained-html",
           "--screenshot=only-on-failure",
           "--video=retain-on-failure",
           f"--output={artifacts_dir}",  # pytest-playwright: where screenshots/videos land
       ] + build_pytest_args(module, smoke)

    result = subprocess.run(args)
    if result.returncode != 0 and not os.path.exists(report_path):
        print(f"\npytest failed before a report could be generated (exit code {result.returncode}).")
    else:
        print(f"\nReport: {report_path}")

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