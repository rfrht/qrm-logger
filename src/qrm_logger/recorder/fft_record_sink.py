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
GNU Radio sink block for recording FFT data.
Captures spectrum data during timed recording intervals for spectrum analysis.
"""

import logging
import time
import zlib
from datetime import datetime

import numpy as np
from gnuradio import gr

from qrm_logger.core.objects import CaptureRun
from qrm_logger.data.fft_data import write_raw
from qrm_logger.utils.perf import log_time_to_first_fft_frame


def current_time():
    return time.time_ns() // 1_000_000


class fft_record_sink(gr.sync_block):
    logger = logging.getLogger(__name__)

    def __init__(self, fft_size):
        self.start_time = None
        self.is_recording = False
        self.is_finalizing = False
        self.rec_time = 5000
        self.fft_size = fft_size
        self.current_run = None
        self.data = []
        self.receiver_started_at_perf = None
        self.first_frame_after_start_logged = False

        gr.sync_block.__init__(self,
                               name="plotter",
                               in_sig=[(np.float32, fft_size)],
                               out_sig=[])

    def mark_receiver_start(self):
        self.receiver_started_at_perf = time.perf_counter()
        self.first_frame_after_start_logged = False

    def work(self, input_items, output_items):
        ninput_items = len(input_items[0])

        # Log time-to-first FFT frame after receiver start
        if ninput_items > 0 and (self.receiver_started_at_perf is not None) and (not self.first_frame_after_start_logged):
            elapsed_ms = (time.perf_counter() - self.receiver_started_at_perf) * 1000.0
            log_time_to_first_fft_frame(elapsed_ms)
            self.first_frame_after_start_logged = True
            self.receiver_started_at_perf = None

        for bins in input_items[0]:
            p = np.around(bins).astype(int)
            p = np.fft.fftshift(p)
            self.process_recording(p)

        self.consume(0, ninput_items)
        return 0

    def start_record(self, run: CaptureRun):
        if self.is_recording:
            logging.warning("record in progress")
            return
        logging.info("Record " + str(run.id) + " | center_frequency=" + str(
            round(run.freq/1000)) + " kHz | span=" + str(round(run.span/1000)) + " kHz | duration=" + str(round(run.rec_time_ms / 1000, 1)) + " s")
        self.rec_time = run.rec_time_ms
        
        # Set the actual capture start time
        run.capture_start_time = datetime.now()

        self.is_recording = True
        self.is_finalizing = False
        self.start_time = current_time()
        self.current_run = run
        self.clear_data()


    def process_recording(self, p):
        if self.is_finalizing:
            return
        if self.is_recording:
            if current_time() - self.start_time < self.rec_time:
                self.data.append(p)
            else:
                #logging.info("record stop")
                self.is_finalizing = True
                self.current_run.raw_filename = self._write_raw_data()
                self.clear_data()
                self.current_run = None
                self.is_recording = False
    #        else:
    #            logging.info("discard data "+str(len(p)))

    def stop_now(self):
        """Finalize and stop the current recording immediately (cooperative cancel)."""
        try:
            if self.is_finalizing:
                # Already finalizing, nothing to do
                return
            if not self.is_recording:
                # Not recording; ensure flags are reset
                self.is_recording = False
                return
            # Prevent further accumulation
            self.is_finalizing = True
            # Write out whatever we have (if any)
            if self.current_run is not None:
                self.current_run.raw_filename = self._write_raw_data() if self.data else None
            # Clear state
            self.clear_data()
            self.current_run = None
            self.is_recording = False
        except Exception as e:
            logging.error(f"stop_now failed: {e}")

    def clear_data(self):
        self.data.clear()

    def get_data(self):
        return self.data.copy()

    def _write_raw_data(self):
        """Write the in-memory data to a raw file at the end of recording"""
        if not self.data:
            logging.error("No data to write to the raw file")
            return None
        
        if not self.current_run:
            logging.error("No current run available for writing raw data")
            return None
        
        return write_raw(self.current_run, self.get_data())
