# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 DO1ZL
# This file is part of qrm-logger.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
qrm-logger entry point module.
Provides a main() function and supports `python -m qrm_logger`.
"""

import argparse
import logging
import time
import json

from gnuradio import gr


def enable_realtime():
    if gr.enable_realtime_scheduling() != gr.RT_OK or 0:
        logging.error("Error: failed to enable real-time scheduling.")


def run_once():
    """Execute a single recording and exit"""
    from qrm_logger.recorder.recorder import get_recorder
    
    enable_realtime()


    try:
        # Use unified parameter object for single recording
        from qrm_logger.core.objects import CaptureParams
        params = CaptureParams(rec_time_sec=None, note="run-once", is_calibration=False)

        logging.info("Starting single recording...")
        # Use Pipeline singleton for capture execution
        from qrm_logger.execution import get_pipeline
        get_pipeline().execute_capture(params)
        logging.info("Recording completed")
    except Exception as e:
        logging.error(f"Recording failed: {e}")
    finally:
        # Clean up GNU Radio resources
        logging.info("Cleaning up resources...")
        get_recorder().disconnect_receiver()

        # Force exit
        logging.info("Exiting")
        import os
        os._exit(0)


def main():

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("Logging configured")

    # Load TOML configuration first (before other imports)
    from qrm_logger.config.toml_config import load_toml_config, load_bands_toml
    load_toml_config()
    logging.info("TOML configuration loaded")
    load_bands_toml()
    logging.info("Band definitions loaded")

    # Import config modules after TOML is loaded
    from qrm_logger.utils.util import  print_capture_set, check_config, check_capture_sets

    from qrm_logger.config.capture_definitions import init_capture_sets
    from qrm_logger.core.config_manager import get_config_manager
    from qrm_logger.scheduling.scheduler import get_scheduler
    from qrm_logger.web.web_routes import run_bottle

    init_capture_sets()
    
    # Validate capture set configuration - exit if invalid
    if not check_capture_sets():
        logging.error("Capture set validation failed. Please fix the configuration errors and restart.")
        import sys
        sys.exit(1)
    
    # Generate ROI config if missing (after capture sets are validated)
    from qrm_logger.data.roi_store import generate_default_roi_config
    generate_default_roi_config()

    # Initialize configuration from JSON file
    logging.info("Initializing configuration...")
    config_data = get_config_manager().get_all()
    logging.info("Configuration loaded:\n%s", json.dumps(config_data, indent=2, sort_keys=True))

    parser = argparse.ArgumentParser()
    parser.add_argument("--run-once", required=False, action='store_true',
                        help="Record once immediately and exit")
    args = parser.parse_args()

    check_config()

    # Print capture set configuration to console
    logging.info("=== Capture Set Configurations ===")
    from qrm_logger.config.capture_definitions import get_capture_sets
    for s in get_capture_sets():
        print_capture_set(s)
    logging.info("===================================")

    enable_realtime()

    if args.run_once:
        run_once()
    else:
        run_bottle()
        logging.info("app started")

        # Conditionally start scheduler based on config
        scheduler_autostart = get_config_manager().get("scheduler_autostart", False)
        if scheduler_autostart:
            logging.info("Auto-starting scheduler based on config setting")
            get_scheduler().start_scheduler()
        else:
            logging.info("Scheduler autostart disabled - use web interface to start manually")

        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()

