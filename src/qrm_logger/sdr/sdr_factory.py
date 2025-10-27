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
SDR device factory for creating GNU Radio source blocks.
"""

import logging

from qrm_logger.core.config_manager import get_config_manager
from qrm_logger.config.sdr_hardware import DEVICE_NAME_RTLSDR, DEVICE_NAME_SDRPLAY, device_name
from qrm_logger.sdr.sdr_rtlsdr import (
    get_rtlsdr, set_rtlsdr_gain,
    RTLSDR_BANDWIDTH_OPTIONS, RTLSDR_BANDWIDTH_DEFAULT,
    RTLSDR_RF_GAIN_MIN, RTLSDR_RF_GAIN_MAX, RTLSDR_RF_GAIN_DEFAULT
)
from qrm_logger.sdr.sdr_sdrplay import (
    get_sdrplay, set_sdrplay_gain,
    SDRPLAY_BANDWIDTH_OPTIONS, SDRPLAY_BANDWIDTH_DEFAULT,
    SDRPLAY_RF_GAIN_MIN, SDRPLAY_RF_GAIN_MAX, SDRPLAY_RF_GAIN_DEFAULT,
    SDRPLAY_IF_GAIN_MIN, SDRPLAY_IF_GAIN_MAX, SDRPLAY_IF_GAIN_DEFAULT
)


def get_sdr(freq, samp_rate):
    logging.info("get sdr: "+device_name)
    
    if device_name == DEVICE_NAME_RTLSDR:
        return get_rtlsdr(freq, samp_rate)
    elif device_name == DEVICE_NAME_SDRPLAY:
        return get_sdrplay(freq, samp_rate)
    else:
        logging.error("get_sdr: unknown device "+device_name)
        return None

def set_sdr_gain(source0, rf_gain, if_gain):
    if device_name == DEVICE_NAME_RTLSDR:
        logging.info("set RF_GAIN = " + str(rf_gain))
        return set_rtlsdr_gain(source0, rf_gain)
    elif device_name == DEVICE_NAME_SDRPLAY:
        logging.info("set RF_GAIN = " + str(rf_gain) + ", IF_GAIN = " + str(if_gain))
        return set_sdrplay_gain(source0, rf_gain, if_gain)
    else:
        logging.error("set_sdr_gain: unknown device "+device_name)
        return None



def get_bandwidth_default():
    """Get default bandwidth for the configured SDR device."""
    if device_name == DEVICE_NAME_RTLSDR:
        return RTLSDR_BANDWIDTH_DEFAULT
    elif device_name == DEVICE_NAME_SDRPLAY:
        return SDRPLAY_BANDWIDTH_DEFAULT
    return 0


def get_bandwidth_options():
    """Get available bandwidth options for the configured SDR device."""
    if device_name == DEVICE_NAME_RTLSDR:
        return RTLSDR_BANDWIDTH_OPTIONS
    elif device_name == DEVICE_NAME_SDRPLAY:
        return SDRPLAY_BANDWIDTH_OPTIONS
    return []


def get_sdr_options():
    """Get all SDR options including bandwidth and gain ranges for the configured device."""
    config_mgr = get_config_manager()
    
    # Base structure with common fields
    options = {
        "device": device_name,
        "bandwidth": {
            "options": [],
            "default": 0,
            "current": config_mgr.get('sdr_bandwidth')
        },
        "rf_gain": {
            "min": 0,
            "max": 0,
            "default": 0,
            "current": config_mgr.get('rf_gain')
        }
    }
    
    # Add device-specific values
    if device_name == DEVICE_NAME_RTLSDR:
        options["bandwidth"].update({
            "options": RTLSDR_BANDWIDTH_OPTIONS,
            "default": RTLSDR_BANDWIDTH_DEFAULT
        })
        options["rf_gain"].update({
            "min": RTLSDR_RF_GAIN_MIN,
            "max": RTLSDR_RF_GAIN_MAX,
            "default": RTLSDR_RF_GAIN_DEFAULT
        })
    elif device_name == DEVICE_NAME_SDRPLAY:
        options["bandwidth"].update({
            "options": SDRPLAY_BANDWIDTH_OPTIONS,
            "default": SDRPLAY_BANDWIDTH_DEFAULT
        })
        options["rf_gain"].update({
            "min": SDRPLAY_RF_GAIN_MIN,
            "max": SDRPLAY_RF_GAIN_MAX,
            "default": SDRPLAY_RF_GAIN_DEFAULT
        })
        options["if_gain"] = {
            "min": SDRPLAY_IF_GAIN_MIN,
            "max": SDRPLAY_IF_GAIN_MAX,
            "default": SDRPLAY_IF_GAIN_DEFAULT,
            "current": config_mgr.get('if_gain')
        }
    
    return options

