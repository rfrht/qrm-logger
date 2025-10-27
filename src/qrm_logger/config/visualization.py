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
Plot and visualization configuration settings for QRM Logger.
Contains image generation, grid layout, plot appearance, and processing control settings.
"""

# =============================================================================
# PLOT/VISUALIZATION CONFIGURATION
# =============================================================================

# Enable drawing of amateur radio band markers on spectrum plots
draw_bandplan = True

# Enable drawing of MHz frequency separators on spectrum plots
draw_mhz_separators = True


# Image compression settings
# PNG compression level (0-9): 0=no compression, 9=maximum compression
# Higher values = smaller files but slower saving
png_compression_level = 6  # Good balance of size and speed

# Grid row sorting order (True = latest first, False = oldest first)
grid_sort_latest_first = True

# FFT decimation for waterfall plots
# decimation_method: Algorithm used when combining adjacent frequency bins
# "mean" - Takes average of decimated bins (smoothest appearance, good for noise floor)
# "max" - Takes maximum of decimated bins (preserves narrow band signals and peaks)
# "sample" - Simple sampling (fastest, may miss signals)
decimation_method = "mean"


# Split daily grids into multiple images by fixed hour windows
# Example: grid_time_window_hours = 6  -> 00-06, 06-12, 12-18, 18-24
# Example: grid_time_window_hours = 12 -> 00-12, 12-24
# Note: Changing this setting during a day will produce mixed windows for that date (old and new labels).
#       To avoid confusion, change it at the start of a new day.
grid_time_window_hours = 12

# Maximum number of recordings to include in grid (0 = unlimited)
# Useful short interval monitoring sessions - shows only most recent N recordings
grid_max_rows = 0  # 0 = show all recordings, >0 = limit to N most recent

# Show grid title label (date) in top-left tile
# If True: Date label appears in top-left corner of the grid
# If False: No title label, grid starts directly with frequency labels
grid_show_title_label = True



# Skip image generation for faster processing (data-only mode)
# If True: Only RMS analysis is performed, no spectrum plots are generated
# If False: Full processing including spectrum plot generation
# Useful for high-frequency monitoring where only CSV data is needed
skip_image_generation = False
