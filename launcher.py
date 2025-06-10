"""Launcher used by packaged binaries to start the NiceGUI app.

Dependencies:
- app.main: Contains the main() function to start the application.

Usage:
Run this script directly to start the NiceGUI application.

Environment:
- APP_CONFIG (optional): path to an application configuration file.

Command-line arguments:
--debug   Run in debug mode (more verbose logging)
"""

import logging
import argparse
import os
import sys

from dotenv import load_dotenv
from app.main import main

def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def check_environment():
    load_dotenv()
    if not os.getenv("APP_CONFIG"):
        logging.warning(
            "APP_CONFIG environment variable is not set; using defaults."
        )

def parse_args():
    parser = argparse.ArgumentParser(description="Launch NiceGUI app.")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode.")
    return parser.parse_args()

# ``ui.run`` needs to be executed even when the script is started via
# ``multiprocessing`` (e.g. when bundled with PyInstaller).  In such
# cases the module name is ``"__mp_main__"``.  We therefore check for
# both names here.
if __name__ in {"__main__", "__mp_main__"}:  # pragma: no cover - manual start
    args = parse_args()
    setup_logging(args.debug)
    logging.info("Launcher started.")
    check_environment()
    try:
        main()
    except Exception as e:
        logging.exception(f"An error occurred while running the app: {e}")
        sys.exit(1)
