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
import time

from gnuradio import gr
from gnuradio.fft import window, logpwrfft
from gnuradio.gr.gr_python import hier_block2_pb

from qrm_logger.core.config_manager import get_config_manager
from qrm_logger.config.recording_params import fft_avg_alpha
from qrm_logger.recorder.fft_record_sink import fft_record_sink
from qrm_logger.sdr.sdr_factory import get_sdr, set_sdr_gain
from qrm_logger.utils.perf import log_perf_sdr_source_creation


class fft_receiver(gr.top_block):

    def __init__(self, samp_rate, freq, fft_size, framerate):
        gr.top_block.__init__(self, "Top Block")

        self.samp_rate = samp_rate
        self.freq = freq
        self.fft_size = fft_size

        logging.info("init FFT: " + str(fft_size))
        avg_alpha = fft_avg_alpha

        '''
        •  Hamming: Mainlobe ~1.30 bins, sidelobes ~ −41 dB. Good compromise; sharper than Hann with better sidelobes.
        •  Hann: Mainlobe ~1.44 bins, sidelobes ~ −31 dB. Slightly wider than Hamming, cleaner than rectangular.
        •  Blackman-Harris (4-term): Mainlobe ~1.9–2.0 bins, sidelobes ~ −90 dB. Very clean floor, but noticeably wider peaks.
        •  Flat-top: Very wide mainlobe (~3.8 bins), very low sidelobes. Great amplitude accuracy, poor apparent sharpness.

        '''

        # win = window.blackmanharris
        win = window.hamming

        self.fft = logpwrfft.logpwrfft_c(
            sample_rate=samp_rate,
            fft_size=fft_size,
            ref_scale=1,
            frame_rate=framerate,
            avg_alpha=avg_alpha,
            average=(avg_alpha != 1),
            win=win
        )

        self.fft_record_sink = fft_record_sink(fft_size)


        ##################################################
        # Blocks
        ##################################################


        t0 = time.perf_counter()
        self.source_0 = get_sdr(freq, samp_rate)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.set_gain()

        ##################################################
        # Connections
        ##################################################

        self.connect((self.source_0, 0), (self.fft, 0))
        self.connect((self.fft, 0), (self.fft_record_sink, 0))

        log_perf_sdr_source_creation(elapsed_ms)



    def set_gain(self):
        if self.source_0:
            rf_gain = get_config_manager().get("rf_gain")
            if_gain = get_config_manager().get("if_gain")
            set_sdr_gain(self.source_0, rf_gain, if_gain)

    def set_frequency(self, v):
        self.source_0.set_center_freq(v)


    def set_sample_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.fft.set_sample_rate(samp_rate)
        try:
            # Propagate sample rate to SDR source if supported
            self.source_0.set_sample_rate(samp_rate)
        except Exception as e:
            logging.info(f"set_sample_rate not supported or failed: {e}")


    def disconnect_all(self):

        if isinstance(self.source_0, hier_block2_pb):
            logging.info("disconnect_all")
            self.source_0.disconnect_all()
        else:
            # sdrplay
            logging.info("disconnect")
            # self.source_0.disconnect()
            self.disconnect(self.source_0, self.fft, self.fft_record_sink)
#        self.fft_record_sink.disconnect_all()
        self.source_0 = None
