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
"""

from qrm_logger.core.objects import Band

# Amateur radio band definitions for plot annotations
# Each Band defines: (name, start_freq_khz, end_freq_khz)
# Used to draw colored band markers on spectrum plots

band_markers = [
    # IARU Region 1 HF
    Band("160m", 1810, 2000),   # 160 meter band
    Band("80m", 3500, 3800),    # 80 meter band
    # Region 2 variant (uncomment to use):
    # Band("80m", 3500, 4000),    # 80/75 meter band (Region 2)
    Band("60m", 5351, 5367),    # 60 meter band
    Band("40m", 7000, 7200),    # 40 meter band
    # Region 2 variant (uncomment to use):
    # Band("40m", 7000, 7300),    # 40 meter band (Region 2)
    Band("30m", 10100, 10150),  # 30 meter band
    Band("20m", 14000, 14350),  # 20 meter band
    Band("17m", 18068, 18168),  # 17 meter band
    Band("15m", 21000, 21450),  # 15 meter band
    Band("12m", 24890, 24990),  # 12 meter band
    Band("10m", 28000, 29700),  # 10 meter band
    # IARU Region 1 VHF/UHF service markers (kHz)
    # 2m satellite downlink (space-to-Earth)
    Band("VHF-SAT-DL", 145800, 146000),
    # 2m FM repeater outputs
    Band("VHF-RPT-OUT", 145600, 145800),

    # 70cm satellite downlink (space-to-Earth)
    Band("UHF-SAT-DL", 435000, 438000),
    # 70cm FM repeater outputs (typical Region 1 allocation; varies nationally)
    Band("UHF-RPT-OUT", 439000, 440000),
]
