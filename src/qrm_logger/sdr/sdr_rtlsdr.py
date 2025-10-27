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

import logging
from qrm_logger.config.sdr_hardware import bias_t_enabled

# RTL-SDR bandwidth options in kHz
RTLSDR_BANDWIDTH_OPTIONS = [250, 1024, 1536, 2048, 2400, 2561, 3200, 4096]
# default for dynamic property 'sdr_bandwidth', managed by config.json
RTLSDR_BANDWIDTH_DEFAULT = 2400

# RTL-SDR gain range
RTLSDR_RF_GAIN_MIN = 0
RTLSDR_RF_GAIN_MAX = 50
RTLSDR_RF_GAIN_DEFAULT = 0


def get_rtlsdr(freq, samp_rate):
    import osmosdr

    # gr-osmosdr 0.2.0.0 (0.2.0) gnuradio 3.10.12.0
    # built-in source types: file rtl rtl_tcp uhd miri hackrf bladerf airspy airspyhf soapy redpitaya

    # this has been tested with RTLSDR v4 only
    # replace the device_name with one of the source types in the list above to run on other SDRs
    # also see here: https://osmocom.org/projects/gr-osmosdr/wiki
    device_name = "rtl"

    device_args = device_name

    device_args += ",numchan=" + str(1)
    device_args += ",bias="+ ("1" if bias_t_enabled else "0")
    if bias_t_enabled:
        logging.info("RTL-SDR Bias-T enabled via device args")
    logging.info("device_args="+str(device_args))

    source_0 = osmosdr.source(args=device_args)

    log_device_info(source_0)

    source_0.set_sample_rate(samp_rate)
    source_0.set_center_freq(freq, 0)

    source_0.set_time_unknown_pps(osmosdr.time_spec_t())
    source_0.set_freq_corr(0, 0)
    source_0.set_dc_offset_mode(0, 0)
    source_0.set_iq_balance_mode(0, 0)
    source_0.set_gain_mode(False, 0)

    source_0.set_antenna('', 0)
    source_0.set_bandwidth(0, 0)
    return source_0

def log_device_info(source_0):
    # Log available device information
    try:
        # Get available gain stages (typically shows tuner type)
        gain_names = source_0.get_gain_names(0)
        if gain_names:
            logging.info(f"RTL-SDR tuner gain stages: {gain_names}")
    except Exception as e:
        logging.debug(f"Could not query RTL-SDR gain stages: {e}")

    try:
        # Get gain range
        gain_range = source_0.get_gain_range(0)
        logging.info(f"RTL-SDR gain range: {gain_range.start()} to {gain_range.stop()} dB (step: {gain_range.step()})")
    except Exception as e:
        logging.debug(f"Could not query RTL-SDR gain range: {e}")

    try:
        # Get bandwidth range
        bandwidth_range = source_0.get_bandwidth_range(0)
        logging.info(
            f"RTL-SDR bandwidth range: {bandwidth_range.start()} to {bandwidth_range.stop()} Hz (step: {bandwidth_range.step()})")
    except Exception as e:
        logging.debug(f"Could not query RTL-SDR bandwidth range: {e}")


def set_rtlsdr_gain(source_0, rf_gain):
    import logging
    
    # Validate RF gain range for RTL-SDR
    # Hardware range: 0.0 to ~49.6 dB (29 discrete steps for R820T/R820T2 tuner)
    # Driver will round to nearest supported value
    if rf_gain < 0 or rf_gain > 50:
        logging.warning(f"RTL-SDR RF gain ({rf_gain} dB) outside valid range: 0-50 dB")
    
    #source_0.set_if_gain(20, 0) # seems unused for rtl
    #source_0.set_bb_gain(20, 0) # seems unused for rtl
    source_0.set_gain(rf_gain, 0)
