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
SDR hardware configuration settings for QRM Logger.
Contains device-specific settings and hardware management options.
"""

from .toml_config import _toml

# =============================================================================
# SDR DEVICE NAME CONSTANTS
# =============================================================================

DEVICE_NAME_RTLSDR = _toml["sdr"]["device_names"]["rtlsdr"]
DEVICE_NAME_SDRPLAY = _toml["sdr"]["device_names"]["sdrplay"]

# =============================================================================
# SDR HARDWARE CONFIGURATION
# =============================================================================

# SDR device type to use
device_name = _toml["sdr"]["device_name"]

# RF gain setting for the SDR device
# for RTLSDR: 0 to 50 dB (discrete steps, typical 0-40 dB). Default: 0 dB
# for SDRPlay RF: 0 to -24 dB (frequency dependent). Recommended value: -18
# dynamic property, managed by config.json
rf_gain = _toml["sdr"]["rf_gain"]

# IF gain setting for the SDR device (SDRPlay only)
# for SDRPlay IF: -20 to -59 dB. Recommended value: -35
# dynamic property, managed by config.json
if_gain = _toml["sdr"]["if_gain"]

# Bias-T power supply setting
# Enables DC voltage on antenna port to power LNAs or other active antennas
# WARNING: Only enable if your antenna/LNA requires bias-T power
# Applies to both RTLSDR (if supported by hardware) and SDRPlay devices
# NOTE: Bias-T will remain active after recording ends. To disable it, set this to False and run another recording.
bias_t_enabled = _toml["sdr"]["bias_t_enabled"]

# Shutdown SDR device after recording to save energy and reduce idle temperature.
# If True: SDR is stopped and fully disconnected between recordings (default).
#   Benefits: Lower idle power, reduced device temperature.
#   Tradeoff: Slightly longer startup time before recording.
# If False: Keep SDR session open between recordings to reduce startup time.
#   Benefits: Faster time to record; maintains stable operating temperature.
#   Tradeoff: Higher continuous energy consumption and device heat.
#   Warning: When this is off, do not unplug the SDR/USB while active; the application cannot reconnect.
# dynamic property, managed by config.json
sdr_shutdown_after_recording = _toml["sdr"]["shutdown_after_recording"]
