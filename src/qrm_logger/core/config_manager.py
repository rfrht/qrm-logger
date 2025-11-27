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
Configuration manager for QRM Logger.
Handles loading configuration from config.json file and creates default config if needed.
"""

import json
import logging
import os
from typing import Dict, Any

# Single source of truth for the JSON config file path (relative to project root)
DEFAULT_CONFIG_PATH = "config.json"

# Import default values from existing config.py
from qrm_logger.config.scheduler_settings import scheduler_cron, scheduler_autostart
from qrm_logger.config.recording_params import rec_time_default_sec, fft_size_default, min_db, max_db
from qrm_logger.config.sdr_hardware import device_name, rf_gain, if_gain, sdr_shutdown_after_recording
from qrm_logger.config.capture_definitions import init_capture_sets, get_capture_set_ids
from qrm_logger.sdr.sdr_rtlsdr import RTLSDR_BANDWIDTH_DEFAULT
from qrm_logger.sdr.sdr_sdrplay import SDRPLAY_BANDWIDTH_DEFAULT
from qrm_logger.config.visualization import timeslice_hours_default, timeslice_autogenerate_default


class ConfigManager:
    """Manages configuration loading from JSON file with fallback to defaults."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config_file_path: str = None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_file_path: str = None):
        # Only initialize once
        if ConfigManager._initialized:
            return
            
        # Resolve the config file path once, in one place
        if not config_file_path:
            config_file_path = DEFAULT_CONFIG_PATH
        self.config_file_path = config_file_path
        self.config_data = {}

        # Initialize capture sets and list IDs (for validation/logging)
        init_capture_sets()
        capture_set_ids = get_capture_set_ids()
        logging.info("capture_set_ids "+ str(capture_set_ids))

        # Get default bandwidth based on device_name from sdr_hardware
        from qrm_logger.config.sdr_hardware import DEVICE_NAME_RTLSDR
        default_bandwidth = RTLSDR_BANDWIDTH_DEFAULT if device_name == DEVICE_NAME_RTLSDR else SDRPLAY_BANDWIDTH_DEFAULT

        # Default configuration values from the original config.py
        self.default_config = {
            "rf_gain": rf_gain,
            "if_gain": if_gain,
            "sdr_bandwidth": default_bandwidth,
            "rec_time_default_sec": rec_time_default_sec,
            "scheduler_cron": scheduler_cron,
            "scheduler_autostart": scheduler_autostart,
            "fft_size": fft_size_default,
            "min_db": min_db,
            "max_db": max_db,
            "capture_sets_enabled": ["HF_bands", "HF_full"],
            "sdr_shutdown_after_recording": sdr_shutdown_after_recording,
            # Per-capture-set configurations (e.g., bandwidth overrides)
            "capture_set_configurations": {},
            # Time-slice (across days) dynamic settings
            "timeslice_hours": timeslice_hours_default,
            "timeslice_autogenerate": timeslice_autogenerate_default,
        }
        
        self.load_config()
        ConfigManager._initialized = True
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file, create with defaults if not found."""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    self.config_data = json.load(f)
                logging.info(f"Configuration loaded from {self.config_file_path}")
                
                # Validate and fill missing keys with defaults
                updated = False
                for key, default_value in self.default_config.items():
                    if key not in self.config_data:
                        self.config_data[key] = default_value
                        updated = True
                        logging.warning(f"Missing config key '{key}', using default: {default_value}")
                
                # Sync capture_sets_enabled with current capture sets and ensure only valid IDs
                try:
                    valid_set_ids_list = get_capture_set_ids()
                except Exception:
                    # Fallback to defaults computed at init if capture sets are unavailable for any reason
                    valid_set_ids_list = list(self.default_config.get('capture_sets_enabled', []))
                valid_set_ids_set = set(valid_set_ids_list)

                existing = self.config_data.get('capture_sets_enabled')
                if not isinstance(existing, list):
                    logging.warning("Config key 'capture_sets_enabled' is not a list; resetting to defaults.")
                    existing = []

                # Filter out any invalid IDs while preserving order
                filtered = [sid for sid in existing if sid in valid_set_ids_set]

                # Do not fallback to enabling all sets; keep only valid IDs present in existing list
                if filtered != existing:
                    removed = set(existing or []) - set(filtered)
                    self.config_data['capture_sets_enabled'] = filtered
                    updated = True
                    if removed:
                        logging.info(f"Removed invalid IDs from capture_sets_enabled: {sorted(list(removed))}")
                
                # Save config if we added missing keys or normalized values
                if updated:
                    logging.info(f"Configuration needs fixing; saving updates to {self.config_file_path}")
                    self.save_config()
                    
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error loading config from {self.config_file_path}: {e}")
                logging.info("Creating new config file with defaults")
                self.config_data = self.default_config.copy()
                self.save_config()
        else:
            logging.info(f"Config file {self.config_file_path} not found, creating with defaults")
            self.config_data = self.default_config.copy()
            self.save_config()
        
        return self.config_data
    
    def save_config(self) -> bool:
        """Save current configuration to JSON file.
        Ensures the parent directory exists before writing.
        """
        try:
            parent = os.path.dirname(os.path.abspath(self.config_file_path))
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            with open(self.config_file_path, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            logging.info(f"Configuration saved to {self.config_file_path}")
            return True
        except IOError as e:
            logging.error(f"Error saving config to {self.config_file_path}: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get configuration value by key."""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save to file."""
        self.config_data[key] = value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration data."""
        return self.config_data.copy()


# Singleton instance function
def get_config_manager() -> ConfigManager:
    """Get the singleton ConfigManager instance"""
    return ConfigManager()

