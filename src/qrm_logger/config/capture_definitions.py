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
Frequency and capture configuration definitions for QRM Logger.
Contains capture set definitions and initialization logic.
"""

import json
import logging
import os

from qrm_logger.core.objects import CaptureSet, CaptureSpec, FreqRange
from qrm_logger.utils.util import create_step_specs, create_band_specs, create_vhf_specs, create_uhf_specs


# =============================================================================
# FREQUENCY/CAPTURE CONFIGURATION
# =============================================================================

# Path to the capture sets configuration file
CAPTURE_SETS_JSON_PATH = "capture_sets.json"

# Current version of the capture sets JSON schema
CAPTURE_SETS_JSON_VERSION = 1

# Global capture_sets list (loaded from JSON)
capture_sets = []

# Note: Capture specs can be added or removed dynamically.
# - Added specs will be appended as new columns in CSV and grid
# - Removed specs will show as -1 in CSV and blank placeholders in grid

# The frequency is always interpreted as center frequency
# It can be useful to have some overlap between the segments


# =============================================================================
# SPEC BUILDER REGISTRY
# =============================================================================

SPEC_BUILDERS = {
    "band_specs": create_band_specs,
    "step_specs": create_step_specs,
    "vhf_specs": lambda **kwargs: create_vhf_specs(),
    "uhf_specs": lambda **kwargs: create_uhf_specs(),
}


# =============================================================================
# DEFAULT CAPTURE SETS (used for initial JSON generation)
# =============================================================================

def create_default_capture_sets_config():
    """
    Create the default capture sets configuration as a JSON-serializable dict.
    This represents the original hardcoded defaults from the Python code.
    """
    return {
        "version": CAPTURE_SETS_JSON_VERSION,
        "capture_sets": [
            {
                "id": "HF_bands",
                "description": "Amateur radio HF bands (80m, 40m, 30m, 20m, 17m, 15m, 10m)",
                "type": "band_specs",
                "params": {
                    "band_ids": ["80m", "40m", "30m", "20m", "17m", "15m", "10m"]
                }
            },
            {
                "id": "HF_full",
                "description": "Complete HF coverage 0-30 MHz in 2 MHz steps (best with 2.4 MHz bandwidth)",
                "type": "step_specs",
                "params": {
                    "start_mhz": 1,
                    "end_mhz": 29,
                    "step_mhz": 2,
                    "suffix": " MHz",
                    "crop_to_step": True,
                    "crop_margin_khz": 5
                }
            },
            {
                "id": "HF_full_wide",
                "description": "Wideband HF coverage 3-30 MHz in 5 MHz steps (best with 6 MHz bandwidth)",
                "type": "step_specs",
                "params": {
                    "start_mhz": 3,
                    "end_mhz": 30,
                    "step_mhz": 5,
                    "suffix": " MHz",
                    "crop_to_step": True,
                    "crop_margin_khz": 5
                }
            },
            {
                "id": "VHF_band",
                "description": "2m amateur band (144-146 MHz)",
                "type": "vhf_specs",
                "params": {}
            },
            {
                "id": "UHF_full",
                "description": "70cm amateur band coverage 430-440 MHz in 2 MHz steps",
                "type": "step_specs",
                "params": {
                    "start_mhz": 431,
                    "end_mhz": 439,
                    "step_mhz": 2,
                    "suffix": " MHz",
                    "crop_to_step": True,
                    "crop_margin_khz": 5
                }
            }
        ]
    }


# =============================================================================
# JSON LOADING/SAVING
# =============================================================================

def load_capture_sets_from_json(json_path):
    """
    Load capture sets from JSON configuration file.
    
    Supports two tiers:
    1. Declarative specs using builder functions (type + params)
    2. Raw spec arrays for complex cases (type: raw_specs)
    
    Args:
        json_path: Path to the JSON configuration file
        
    Returns:
        List of CaptureSet objects
        
    Raises:
        ValueError: If version is missing or incompatible
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Check version
    file_version = data.get("version")
    if file_version is None:
        raise ValueError(
            f"Missing 'version' field in {json_path}. "
            f"Expected version {CAPTURE_SETS_JSON_VERSION}."
        )
    
    if file_version != CAPTURE_SETS_JSON_VERSION:
        raise ValueError(
            f"Incompatible capture_sets.json version: {file_version}. "
            f"Expected version {CAPTURE_SETS_JSON_VERSION}. "
            f"Please update or regenerate the file."
        )
    
    capture_sets = []
    
    for set_config in data.get("capture_sets", []):
        set_id = set_config["id"]
        spec_type = set_config["type"]
        
        # Tier 1: Declarative specs using builder functions
        if spec_type in SPEC_BUILDERS:
            params = set_config.get("params", {})
            description = set_config.get("description")
            builder = SPEC_BUILDERS[spec_type]
            specs = builder(**params)
            capture_sets.append(CaptureSet(set_id, specs, description=description))
        
        # Tier 2: Raw specs (for complex cases)
        elif spec_type == "raw_specs":
            raw_specs = set_config.get("specs", [])
            description = set_config.get("description")
            specs = []
            for spec_data in raw_specs:
                # Reconstruct FreqRange if present
                freq_range = None
                if "freq_range" in spec_data:
                    fr = spec_data["freq_range"]
                    freq_range = FreqRange(
                        id=fr["id"],
                        freq_start=fr["freq_start"],
                        freq_end=fr["freq_end"],
                        crop_margin_khz=fr.get("crop_margin_khz", 0)
                    )
                
                # Create CaptureSpec
                spec = CaptureSpec(
                    spec_index=spec_data["spec_index"],
                    id=spec_data["id"],
                    freq=spec_data["freq"],
                    span=spec_data.get("span"),
                    freq_range=freq_range
                )
                specs.append(spec)
            
            capture_sets.append(CaptureSet(set_id, specs, description=description))
        
        else:
            logging.warning(f"Unknown spec type '{spec_type}' for capture set '{set_id}', skipping")
    
    return capture_sets


def save_capture_sets_to_json(config_dict, json_path):
    """
    Save capture sets configuration to JSON file.
    
    Args:
        config_dict: Configuration dictionary (from create_default_capture_sets_config())
        json_path: Path where JSON file should be saved
    """
    with open(json_path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    logging.info(f"Capture sets configuration saved to {json_path}")


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_capture_sets():
    """
    Load capture sets from JSON file, or generate defaults if missing.
    
    Priority:
    1. Load from capture_sets.json (user configuration)
    2. If missing, generate from defaults and save to JSON
    
    Returns:
        List of CaptureSet objects
    """
    global capture_sets
    
    # Try to load from JSON
    if os.path.exists(CAPTURE_SETS_JSON_PATH):
        try:
            capture_sets = load_capture_sets_from_json(CAPTURE_SETS_JSON_PATH)
            logging.info(f"Loaded {len(capture_sets)} capture sets from {CAPTURE_SETS_JSON_PATH}")
            return
        except Exception as e:
            logging.error(f"Error loading capture sets from {CAPTURE_SETS_JSON_PATH}: {e}")
            logging.info("Falling back to default configuration")
    
    # Generate and save defaults
    logging.info(f"{CAPTURE_SETS_JSON_PATH} not found, creating with default configuration")
    default_config = create_default_capture_sets_config()
    
    try:
        save_capture_sets_to_json(default_config, CAPTURE_SETS_JSON_PATH)
        capture_sets = load_capture_sets_from_json(CAPTURE_SETS_JSON_PATH)
        logging.info(f"Created default capture sets configuration with {len(capture_sets)} sets")
    except Exception as e:
        logging.error(f"Error creating default capture sets: {e}")


def get_capture_set_ids():
    """Return list of capture set IDs currently loaded."""
    return [s.id for s in capture_sets]
