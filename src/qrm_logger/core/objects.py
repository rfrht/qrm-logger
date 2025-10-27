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
Data model classes for spectrum analysis system.
Defines structures for captures, capture sets, recordings, frequency bands, and analysis results.
"""

class Band:
    def __init__(self, id, start, end):
        self.id = id
        self.start = start
        self.end = end


class FreqRange:
    def __init__(self, id, freq_start, freq_end, crop_margin_khz=0):
        """
        Frequency range specification for spectrum cropping.
        - id: human-readable identifier (e.g., band label)
        - freq_start: start frequency in kHz
        - freq_end: end frequency in kHz
        - crop_margin_khz: margin to add on each side in kHz (default: 0)
        """
        self.id = id
        self.freq_start = freq_start
        self.freq_end = freq_end
        self.crop_margin_khz = crop_margin_khz


class CaptureSpec:
    def __init__(self, spec_index, id, freq, span=None, freq_range=None):
        """
        Immutable configuration describing what to capture.
        - spec_index: position of this spec within a CaptureSet
        - id: human-readable identifier (e.g., band label)
        - freq: center frequency in kHz
        - span: optional span in kHz (None → use SDR bandwidth)
        - freq_range: optional FreqRange object for spectrum cropping
        """
        self.spec_index = spec_index
        self.id = id
        self.freq = freq
        self.span = span
        self.freq_range = freq_range


class CaptureRun:
    def __init__(self, id, freq, span, position, counter, capture_set_id, date_string, fft_size, rec_time_ms,
                 time, spec=None):
        """
        Runtime instance created from a CaptureSpec.
        - id: spec id
        - freq/span: in Hz at runtime (original requested recording parameters)
        - freq_effective/span_effective: in Hz, post-crop values used by downstream processing/plotting
        - position: spec_index from the spec
        - counter: global run counter
        - capture_set_id: the set this run belongs to
        - date_string: YYYY-MM-DD
        - fft_size, rec_time (ms), is_calibration
        - time: datetime (recording session start time)
        - capture_start_time: datetime (actual capture start time for this individual run)
        - spec: reference to originating CaptureSpec (contains freq_range info)
        """
        self.id = id
        # Original recording parameters (used for SDR tuning)
        self.freq = freq
        self.span = span
        # Effective parameters after any cropping (used for analysis/plotting)
        self.freq_effective = freq
        self.span_effective = span
        
        self.position = position
        self.counter = counter
        self.capture_set_id = capture_set_id
        self.date_string = date_string
        self.fft_size = fft_size
        self.rec_time_ms = rec_time_ms
        self.time = time
        self.capture_start_time = None  # Will be set when actual recording starts
        self.spec = spec
        self.raw_filename = None
        # Optional ROI label used for downstream labeling and filenames
        self.roi_id = None


class CaptureSet:
    def __init__(self, id, specs):
        self.id = id
        self.specs = specs



class RecordingStatus:
    def __init__(self):
        self.operation = None
        self.current_job_number = 0
        self.jobs_total_number = 0
        self.is_error = False
        self.cancel_requested = False


class ProcessingResult:
    def __init__(self):
        self.run = None
        self.raw_filename = None  # Path to raw file containing the FFT data
        self.rms_normalized = None
        self.rms_truncated = None  # 5% truncated RMS for robust interference detection
        self.min_db = None  # Min dB value used for normalization (for calibration mode)
        self.max_db = None  # Max dB value used for normalization (for calibration mode)
        self.is_calibration = False  # Flag to indicate if this is a calibration result
        self.log_text = None


class CaptureParams:
    """
    Container for 'record once' request parameters coming from the UI.

    Attributes:
        rec_time_sec (int|None): Recording time in seconds (None to use config default)
        note (str|None): Optional note
        is_calibration (bool): Calibration mode flag
    """
    def __init__(self, rec_time_sec, note, is_calibration, counter = None, recording_start_datetime = None):
        self.rec_time_sec = rec_time_sec
        self.note = note
        self.is_calibration = is_calibration or False
        self.counter = counter
        self.recording_start_datetime = recording_start_datetime
        self.min_db_val = None
        self.max_db_val = None
