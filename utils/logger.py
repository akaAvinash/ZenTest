"""
Shared logger for the whole ZenTest framework — the backend (database/api.py),
the CLI (cli.py), and the UI test suite (tests/UI_tests/) all import this
same module so log output is consistent everywhere.

Where the log file goes:
  - By default, logs/zentest.log at the repo root (used by the backend when
    run standalone, and by the test suite when run without the CLI).
  - When cli.py runs a test suite via `--start`, it points this at that
    run's own report folder (reports/zentest_report_<timestamp>/zentest.log)
    by setting the ZENTEST_LOG_DIR environment variable before launching
    pytest, so each run's log file ships inside its own report folder
    alongside zentest_report.html.

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Product created: %s", product_id)
"""

import logging
import os
from pathlib import Path

_DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_ENV_VAR = "ZENTEST_LOG_DIR"

# name -> Path of the directory it's currently configured to log into, so a
# repeat get_logger() call with a different target (e.g. cli.py's own
# logger, reconfigured once the report folder is known) re-attaches handlers
# instead of silently keeping the old ones.
_configured: dict[str, Path] = {}


def _resolve_log_dir(log_dir) -> Path:
    if log_dir is not None:
        return Path(log_dir)
    env_dir = os.environ.get(_ENV_VAR)
    if env_dir:
        return Path(env_dir)
    return _DEFAULT_LOG_DIR


def get_logger(name: str = "zentest", log_dir: "str | Path | None" = None) -> logging.Logger:
    """Return a logger that writes to both the console and <log_dir>/zentest.log.

    `log_dir` normally shouldn't be passed explicitly — leave it unset and
    the logger picks up ZENTEST_LOG_DIR (set by cli.py for a given run) or
    falls back to the repo's logs/ folder. Safe to call repeatedly with the
    same name; handlers are only reattached when the resolved directory
    actually changes, so log lines are never duplicated.
    """
    target_dir = _resolve_log_dir(log_dir)

    if _configured.get(name) == target_dir:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    target_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(target_dir / "zentest.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured[name] = target_dir
    return logger
