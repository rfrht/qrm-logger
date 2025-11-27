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

# Global config cache
_config = None

# Config file path (relative to project root)
CONFIG_TOML_PATH = "config.toml"


def _count_keys(d, prefix=""):
    """Recursively count all keys in nested dict."""
    count = 0
    for key, value in d.items():
        if isinstance(value, dict):
            count += _count_keys(value, prefix=f"{prefix}{key}.")
        else:
            count += 1
    return count


def load_toml_config():
    """
    Load config.toml or generate from defaults.
    
    Returns:
        dict: Loaded TOML configuration
    """
    global _config
    
    if _config is not None:
        return _config
    
    # Check if config.toml exists
    if os.path.exists(CONFIG_TOML_PATH):
        try:
            with open(CONFIG_TOML_PATH, "rb") as f:
                _config = tomllib.load(f)
            key_count = _count_keys(_config)
            section_count = len(_config)
            logging.info(f"Loaded configuration from {CONFIG_TOML_PATH}: {section_count} sections, {key_count} keys")
            return _config
        except Exception as e:
            logging.error(f"Error loading {CONFIG_TOML_PATH}: {e}")
            logging.info("Falling back to default configuration")
            _config = _parse_default_config()
            key_count = _count_keys(_config)
            logging.info(f"Using default configuration: {len(_config)} sections, {key_count} keys")
            return _config
    
    # Generate default config.toml
    logging.info(f"{CONFIG_TOML_PATH} not found, creating with defaults")
    try:
        with open(CONFIG_TOML_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_TOML)
        logging.info(f"Created default {CONFIG_TOML_PATH}")
        
        # Load the newly created file
        with open(CONFIG_TOML_PATH, "rb") as f:
            _config = tomllib.load(f)
        key_count = _count_keys(_config)
        section_count = len(_config)
        logging.info(f"Loaded configuration: {section_count} sections, {key_count} keys")
        return _config
    except Exception as e:
        logging.error(f"Error creating {CONFIG_TOML_PATH}: {e}")
        logging.info("Using in-memory default configuration")
        _config = _parse_default_config()
        key_count = _count_keys(_config)
        logging.info(f"Using default configuration: {len(_config)} sections, {key_count} keys")
        return _config


def _parse_default_config():
    """
    Parse default configuration from template string.
    Used as fallback when config.toml cannot be loaded or created.
    
    Returns:
        dict: Parsed default configuration
    """
    return tomllib.loads(DEFAULT_CONFIG_TOML)


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
