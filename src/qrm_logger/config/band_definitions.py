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
Amateur radio band definitions for spectrum analysis and plot annotations.
Loaded from config-bandplan.toml file.
"""

import logging
from qrm_logger.core.objects import Band


def _load_bands_from_toml():
    """
    Load band definitions from config-bandplan.toml.
    
    Returns:
        List of Band objects
    """
    from .toml_config import load_bands_toml
    
    try:
        bands_data = load_bands_toml()
        bands = []
        
        # Each top-level key is a band ID
        for band_id, band_info in bands_data.items():
            band = Band(
                id=band_id,
                start=band_info["start_khz"],
                end=band_info["end_khz"]
            )
            bands.append(band)
        
        logging.info(f"Loaded {len(bands)} band definitions from config-bandplan.toml")
        return bands
        
    except Exception as e:
        logging.error(f"Error loading bands from TOML: {e}")
        logging.info("Using hardcoded fallback bands")
        return _get_fallback_bands()


def _get_fallback_bands():
    """
    Fallback band definitions if config-bandplan.toml cannot be loaded.
    
    Returns:
        List of Band objects with default IARU Region 1 bands
    """
    return [
        # IARU Region 1 HF
        Band("160m", 1810, 2000),
        Band("80m", 3500, 3800),
        Band("60m", 5351, 5367),
        Band("40m", 7000, 7200),
        Band("30m", 10100, 10150),
        Band("20m", 14000, 14350),
        Band("17m", 18068, 18168),
        Band("15m", 21000, 21450),
        Band("12m", 24890, 24990),
        Band("10m", 28000, 29700),
        # VHF/UHF
        Band("VHF-SAT-DL", 145800, 146000),
        Band("VHF-RPT-OUT", 145600, 145800),
        Band("UHF-SAT-DL", 435000, 438000),
        Band("UHF-RPT-OUT", 439000, 440000),
    ]


# Load band markers from TOML
band_markers = _load_bands_from_toml()
