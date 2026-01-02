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
Default TOML band definitions template for QRM Logger.
This template is used to generate config-bandplan.toml on first start.
"""

DEFAULT_BANDS_TOML = """# Amateur Radio Band Definitions for QRM Logger
# Used for spectrum plot annotations and band-specific capture configurations
#
# Structure: [band_id]
# - band_id: Unique identifier used in config-capture_sets.json
# - start_khz: Band start frequency in kHz
# - end_khz: Band end frequency in kHz
#
# Band IDs must be unique across the entire file!
# Default: IARU Region 1 (Europe, Africa, Middle East, Northern Asia)

# =============================================================================
# HF BANDS (High Frequency - 3-30 MHz)
# =============================================================================

[160m]
description = "160 meter band (1.8 MHz)"
start_khz = 1810
end_khz = 2000

[80m]
description = "80 meter band (3.5 MHz)"
# Region 1: 3500-3800 kHz
start_khz = 3500
end_khz = 3800
# Region 2 (Americas): Uncomment below for wider allocation
# start_khz = 3500
# end_khz = 4000

[60m]
description = "60 meter band (5 MHz)"
start_khz = 5351
end_khz = 5367

[40m]
description = "40 meter band (7 MHz)"
# Region 1: 7000-7200 kHz
start_khz = 7000
end_khz = 7200
# Region 2 (Americas): Uncomment below for wider allocation
# start_khz = 7000
# end_khz = 7300

[30m]
description = "30 meter band (10 MHz)"
start_khz = 10100
end_khz = 10150

[20m]
description = "20 meter band (14 MHz)"
start_khz = 14000
end_khz = 14350

[17m]
description = "17 meter band (18 MHz)"
start_khz = 18068
end_khz = 18168

[15m]
description = "15 meter band (21 MHz)"
start_khz = 21000
end_khz = 21450

[12m]
description = "12 meter band (24 MHz)"
start_khz = 24890
end_khz = 24990

[10m]
description = "10 meter band (28 MHz)"
start_khz = 28000
end_khz = 29700

[6m]
description = "6 meter band (50 MHz, lower part)"
start_khz = 50000
end_khz = 52000

# =============================================================================
# VHF/UHF BANDS AND SERVICES
# =============================================================================

[VHF-SAT-DL]
description = "2m satellite downlink (145.8-146.0 MHz)"
# Space-to-Earth communications
start_khz = 145800
end_khz = 146000

[VHF-RPT-OUT]
description = "2m FM repeater outputs (145.6-145.8 MHz)"
# Region 1 typical allocation (varies by country)
start_khz = 145600
end_khz = 145800

[UHF-SAT-DL]
description = "70cm satellite downlink (435-438 MHz)"
# Space-to-Earth communications
start_khz = 435000
end_khz = 438000

[UHF-RPT-OUT]
description = "70cm FM repeater outputs (439-440 MHz)"
# Region 1 typical allocation (varies nationally)
start_khz = 439000
end_khz = 440000

# =============================================================================
# NOTES
# =============================================================================
#
# Band IDs are referenced in config-capture_sets.json
# Example: "band_ids": ["80m", "40m", "30m", "20m"]
#
# To add custom bands:
# 1. Add new [band_id] section with unique ID
# 2. Reference band_id in config-capture_sets.json
#
# Regional differences:
# - Region 1: Europe, Africa, Middle East, Northern Asia
# - Region 2: North/South America
# - Region 3: Asia-Pacific (similar to Region 1 for most HF bands)
"""
