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


from qrm_logger.core.objects import CaptureSet
from qrm_logger.utils.util import create_step_specs, create_band_specs, create_vhf_specs, create_uhf_specs


# =============================================================================
# FREQUENCY/CAPTURE CONFIGURATION
# =============================================================================

capture_sets = []

# Note: Capture specs can be added or removed dynamically.
# - Added specs will be appended as new columns in CSV and grid
# - Removed specs will show as -1 in CSV and blank placeholders in grid

# The frequency is always interpreted as center frequency
# It can be useful to have some overlap between the segments

def init_capture_sets():

    set_hf_bands = CaptureSet(
        id = "HF_bands",
        specs = create_band_specs(
            band_ids = [ "80", "40", "30", "20", "17", "15",  "10" ],
            suffix = "m"
        )
    )
    capture_sets.append(set_hf_bands)

    set_hf_full = CaptureSet(
        id = "HF_full",
        specs = create_step_specs(
            start_mhz = 1,
            end_mhz = 29,
            step_mhz = 2,
            suffix = " MHz",
            crop_to_step = True,
            crop_margin_khz= 5
        )
    )
    capture_sets.append(set_hf_full)

    # for wideband SDR (this works well with SDRPlay bandwidth 6 MHz)
    set_hf_full_wide = CaptureSet(
        id = "HF_full_wide",
        specs = create_step_specs(
            start_mhz = 3,
            end_mhz = 30,
            step_mhz = 5,
            suffix = " MHz",
            crop_to_step = True,
            crop_margin_khz = 5
        )
    )
    capture_sets.append(set_hf_full_wide)

    set_vhf_band = CaptureSet("VHF_band", create_vhf_specs())
    capture_sets.append(set_vhf_band)

    set_uhf_full = CaptureSet(
        id = "UHF_full",
        specs = create_step_specs(
            start_mhz = 431,
            end_mhz = 439,
            step_mhz = 2,
            suffix = " MHz",
            crop_to_step = True,
            crop_margin_khz= 5
        )
    )
    capture_sets.append(set_uhf_full)

