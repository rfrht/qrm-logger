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

# SDRPlay bandwidth options in kHz
SDRPLAY_BANDWIDTH_OPTIONS = [200, 300, 600, 1536, 5000, 6000, 7000, 8000]
# default for dynamic property 'sdr_bandwidth', managed by config-dynamic.json
SDRPLAY_BANDWIDTH_DEFAULT = 6000

# SDRPlay RF gain range (0 to -24 dB, frequency dependent)
SDRPLAY_RF_GAIN_MIN = -24
SDRPLAY_RF_GAIN_MAX = 0
SDRPLAY_RF_GAIN_DEFAULT = -18


# RF gain has limited steps on the lower frequencies:
#
#const std::vector<int> rsp1a_impl::rf_gr_values(const double freq)
#    if (freq <= 60e6) {
#        static const std::vector<int> rf_gr = { 0, 6, 12, 18, 37, 42, 61 };
#        return rf_gr;
#    } else if (freq <= 420e6) {
#        static const std::vector<int> rf_gr = { 0, 6, 12, 18, 20, 26, 32, 38, 57, 62 };
#        return rf_gr;
#    } else if


# SDRPlay IF gain range (-59 to -20 dB)
SDRPLAY_IF_GAIN_MIN = -59
SDRPLAY_IF_GAIN_MAX = -20
SDRPLAY_IF_GAIN_DEFAULT = -40


def get_sdrplay(freq, samp_rate):
    from gnuradio import sdrplay3

    # gr-sdrplay3
    # https://github.com/fventuri/gr-sdrplay3

    # This module supports the following SDRplay RSP devices:
    #  - RSP1  - RSP1A  - RSP1B  - RSP2
    #  - RSPduo  - RSPdx  - RSPdx-R2
    # This module requires SDRplay API version 3.x (at least version 3.15) to work.

    args = sdrplay3.stream_args(output_type = 'fc32', channels_size = 1)

    # this was tested on the RSP1A only
    # to run on other sdrplay devices, replace the following line
    # possible device names here: https://github.com/fventuri/gr-sdrplay3/tree/main/include/gnuradio/sdrplay3
    
    sdrplay3_rsp_0 = sdrplay3.rsp1a("", stream_args = args)
    
    log_device_info(sdrplay3_rsp_0)

    # RSPA1 : Sampling rate vs Bandwidth
    # https://www.sdrplay.com/community/viewtopic.php?t=4520

    sdrplay3_rsp_0.set_sample_rate(samp_rate)
    sdrplay3_rsp_0.set_center_freq(freq)
    sdrplay3_rsp_0.set_bandwidth(0)
    sdrplay3_rsp_0.set_gain_mode(False)

    sdrplay3_rsp_0.set_freq_corr(0)

    sdrplay3_rsp_0.set_dc_offset_mode(False)
    sdrplay3_rsp_0.set_iq_balance_mode(False)

    sdrplay3_rsp_0.set_agc_setpoint((-30))

    sdrplay3_rsp_0.set_rf_notch_filter(False)
    sdrplay3_rsp_0.set_dab_notch_filter(False)
    sdrplay3_rsp_0.set_biasT(bias_t_enabled)
    if bias_t_enabled:
        logging.info("SDRplay Bias-T enabled")
    sdrplay3_rsp_0.set_debug_mode(False)
    sdrplay3_rsp_0.set_sample_sequence_gaps_check(False)
    sdrplay3_rsp_0.set_show_gain_changes(False)
    return sdrplay3_rsp_0

def log_device_info(sdrplay3_rsp_0):
    # Log available device information
    try:
        # Get available gain names (RF, IF, LNAstate)
        gain_names = sdrplay3_rsp_0.get_gain_names()
        if gain_names:
            logging.info(f"SDRplay gain stages: {gain_names}")

        # Get gain ranges for each stage
        for gain_name in gain_names:
            gain_range = sdrplay3_rsp_0.get_gain_range(gain_name)
            logging.info(
                f"SDRplay {gain_name} gain range: {gain_range.start()} to {gain_range.stop()} dB (step: {gain_range.step()})")
    except Exception as e:
        logging.debug(f"Could not query SDRplay device info: {e}")


def set_sdrplay_gain(source_0, rf_gain, if_gain):

    # source_0.set_gain(-35, 'IF')
    # source_0.set_gain(-30, 'RF')
    # source_0.set_gain(0, 'LNAstate')

    # see section 5 https://www.sdrplay.com/docs/SDRplay_SDR_API_Specification.pdf
    # https://www.sdrplay.com/community/viewtopic.php?t=2945
    # https://groups.io/g/openwebrx/topic/sdrplay_gains_implemented/93240851
    # https://github.com/pothosware/SoapySDRPlay3/issues/35
    # https://github.com/pothosware/SoapySDRPlay3/pull/25

    # more on gain ranges here: https://github.com/fventuri/gr-sdrplay3/issues/20
    # the IF gain goes from -20 (highest signal gain) to -59 (lowest signal gain)
    # the gain values for the RF gain go from 0 (highest signal gain of the RF chain) to -N,
    # where the value of N depends on the specific RSP device and frequency band,

    log_gain_settings(source_0, "Gain before:")

    # Validate SDRPlay RF gain range: 0 to -60 dB
    if rf_gain > 0:
        logging.warning(f"SDRPlay RF gain ({rf_gain} dB) outside valid range: 0 to -60 dB (clamped to 0)")
        rf_gain = 0
    elif rf_gain < -60:
        logging.warning(f"SDRPlay RF gain ({rf_gain} dB) outside valid range: 0 to -60 dB")
    
    # Validate SDRPlay IF gain range: -20 to -59 dB
    if if_gain > -20:
        logging.warning(f"SDRPlay IF gain ({if_gain} dB) outside valid range: -20 to -59 dB (clamped to -20)")
        if_gain = -20
    elif if_gain < -59:
        logging.warning(f"SDRPlay IF gain ({if_gain} dB) outside valid range: -20 to -59 dB (clamped to -59)")
        if_gain = -59

    source_0.set_gain(rf_gain, 'RF')
    source_0.set_gain(if_gain, 'IF')

    log_gain_settings(source_0, "Gain after:")


def log_gain_settings(source_0, prefix):
    logging.info(prefix + " IF=" + str(source_0.get_gain('IF')) + ", RF=" + str(source_0.get_gain('RF')) + ", LNAstate=" + str(source_0.get_gain('LNAstate')))
