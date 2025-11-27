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
TOML configuration loader for QRM Logger.
Loads config.toml from project root, generates from defaults if missing.
"""

import os
import logging

# Try tomllib (Python 3.11+), fall back to tomli
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        raise ImportError(
            "TOML support requires Python 3.11+ or the 'tomli' package. "
            "Install with: pip install tomli"
        )

from .configuration_defaults import DEFAULT_CONFIG_TOML
from .band_defaults import DEFAULT_BANDS_TOML

# Global config caches
_config = None
_bands_config = None

# Config file paths (relative to project root)
CONFIG_TOML_PATH = "config.toml"
BANDS_TOML_PATH = "bands.toml"


def _count_keys(d, prefix=""):
    """Recursively count all keys in nested dict."""
    count = 0
    for key, value in d.items():
        if isinstance(value, dict):
            count += _count_keys(value, prefix=f"{prefix}{key}.")
        else:
            count += 1
    return count


def _load_toml_file(file_path, default_content, description="configuration"):
    """
    Generic TOML file loader with auto-generation.
    
    Args:
        file_path: Path to TOML file
        default_content: Default TOML content string
        description: Description for logging
    
    Returns:
        dict: Loaded TOML data
    """
    # Check if file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
            key_count = _count_keys(data)
            section_count = len(data)
            logging.info(f"Loaded {description} from {file_path}: {section_count} sections, {key_count} keys")
            return data
        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
            logging.info(f"Falling back to default {description}")
            data = tomllib.loads(default_content)
            key_count = _count_keys(data)
            logging.info(f"Using default {description}: {len(data)} sections, {key_count} keys")
            return data
    
    # Generate default file
    logging.info(f"{file_path} not found, creating with defaults")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(default_content)
        logging.info(f"Created default {file_path}")
        
        # Load the newly created file
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        key_count = _count_keys(data)
        section_count = len(data)
        logging.info(f"Loaded {description}: {section_count} sections, {key_count} keys")
        return data
    except Exception as e:
        logging.error(f"Error creating {file_path}: {e}")
        logging.info(f"Using in-memory default {description}")
        data = tomllib.loads(default_content)
        key_count = _count_keys(data)
        logging.info(f"Using default {description}: {len(data)} sections, {key_count} keys")
        return data


def load_toml_config():
    """
    Load config.toml or generate from defaults.
    
    Returns:
        dict: Loaded TOML configuration
    """
    global _config
    if _config is None:
        _config = _load_toml_file(CONFIG_TOML_PATH, DEFAULT_CONFIG_TOML, "configuration")
    return _config


def load_bands_toml():
    """
    Load bands.toml or generate from defaults.
    
    Returns:
        dict: Loaded band definitions
    """
    global _bands_config
    if _bands_config is None:
        _bands_config = _load_toml_file(BANDS_TOML_PATH, DEFAULT_BANDS_TOML, "band definitions")
    return _bands_config


class _LazyTomlConfig:
    """Lazy-loading wrapper for TOML config that behaves like a dict."""
    def __getitem__(self, key):
        global _config
        if _config is None:
            _config = load_toml_config()
        return _config[key]
    
    def get(self, key, default=None):
        global _config
        if _config is None:
            _config = load_toml_config()
        return _config.get(key, default)


# Lazy-loading accessor that acts like a dict
_toml = _LazyTomlConfig()
