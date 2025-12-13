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
Output directory and file path configuration for QRM Logger.
Contains base directory settings and subdirectory structure definitions.
"""

from .toml_config import _toml

# =============================================================================
# OUTPUT DIRECTORY CONFIGURATION
# =============================================================================

# Base output directory for all generated files
output_directory = _toml["paths"]["output_directory"]

# Keep raw files after plot generation
# If False: raw files are deleted after plots are created (saves disk space)
# If True: raw files are preserved for later analysis or debugging
keep_raw_files = _toml["paths"]["keep_raw_files"]


# =============================================================================
# SUBDIRECTORY CONSTANTS
# =============================================================================

# Subdirectories for different types of output files
subdirectory_plots_full = "plots_full"       # Full-size spectrum plot images
subdirectory_plots_resized = "plots_resized" # Thumbnail-sized plot images for grids
subdirectory_grids_full = "grids_full"        # Full-size combined grid images
subdirectory_grids_resized = "grids_resized"  # Resized grid images for UI
subdirectory_csv = "csv"                     # CSV data export files
subdirectory_log = "log"                     # Processing logs CSV files
subdirectory_metadata = "metadata"           # Plot metadata and recording details
subdirectory_raw = "raw"                     # Raw FFT data files (compressed)
