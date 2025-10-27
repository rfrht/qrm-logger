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
Analysis configuration settings for QRM Logger.
Contains frequency exclusion and signal analysis parameters.
"""

# =============================================================================
# ANALYSIS CONFIGURATION
# =============================================================================

# Frequencies to exclude from RMS analysis (kHz)
#  - 0 kHz targets baseband/DC artifacts
#  - 28800 kHz is the RTL-SDR Blog V4 upconverter LO frequency
exclude_freqs_khz = [0.0, 28800.0]

