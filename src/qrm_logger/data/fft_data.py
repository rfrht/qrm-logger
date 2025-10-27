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
import os
import zlib
import time
from io import BytesIO

import numpy as np

from qrm_logger.config.output_directories import subdirectory_raw
from qrm_logger.core.objects import CaptureRun
from qrm_logger.utils.util import create_dirname, create_filename, create_filename_raw
from qrm_logger.utils.perf import log_raw_write_perf
from qrm_logger.data.log import collect_log_text


def load_and_crop_data(run):
    """Load raw data once and apply cropping if needed.

    Returns:
        tuple: (data, cropped_data) - original data, and cropped data (or None)
    """
    raw_filename = run.raw_filename

    # Load raw data
    data = load_raw_fft_data(raw_filename, run.fft_size)
    if data is None:
        collect_log_text(run, 'load_and_crop_data', f"ERROR: Failed to load raw data for run {run.id}: {raw_filename}")
        return None, None

    collect_log_text(run, 'load_and_crop_data', f"Loaded raw data from {raw_filename}: shape {data.shape}")

    cropped_data = None
    # Apply cropping if FreqRange is defined
    if run.spec and run.spec.freq_range is not None:
        try:
            # Store original parameters for reference
            original_freq_hz = run.freq
            original_span_hz = run.span
            center_frequency = original_freq_hz / 1000  # Convert Hz to kHz
            span = original_span_hz / 1000  # Convert Hz to kHz

            # Use FreqRange with configurable crop margin
            freq_range = run.spec.freq_range
            margin_khz = freq_range.crop_margin_khz
            crop_start_freq = freq_range.freq_start - margin_khz
            crop_end_freq = freq_range.freq_end + margin_khz

            # Apply cropping
            cropped_data, actual_start, actual_end, start_bin, end_bin = crop_waterfall_spectrum(
                data, center_frequency, span, crop_start_freq, crop_end_freq, run
            )

            # Update effective run parameters to match the cropped spectrum (do not mutate original freq/span)
            run.freq_effective = int((actual_start + actual_end) / 2 * 1000)  # New center in Hz
            run.span_effective = int((actual_end - actual_start) * 1000)       # New span in Hz

            # Collect cropping results
            collect_log_text(run, 'load_and_crop_data', f"Cropping applied to {run.id}:")
            collect_log_text(run, 'load_and_crop_data', f"  FreqRange: {freq_range.id}m ({freq_range.freq_start}-{freq_range.freq_end} kHz)")
            collect_log_text(run, 'load_and_crop_data', f"  Original: {center_frequency:.1f} ± {span /2:.1f} kHz")
            collect_log_text(run, 'load_and_crop_data', f"  Cropped: {actual_start:.1f} - {actual_end:.1f} kHz (margin: {margin_khz} kHz)")
        except Exception as e:
            collect_log_text(run, 'load_and_crop_data', f"WARNING: Failed to crop spectrum for run {run.id} (freq_range {run.spec.freq_range.id}): {e}")
            collect_log_text(run, 'load_and_crop_data', "WARNING: Continuing with full spectrum data")
            # Continue with original data if cropping fails

    return data, cropped_data


def load_raw_fft_data(raw_filename, fft_size=None):
    """Load FFT data from compressed NPY (NumPy) raw file.
    
    The file format is: zlib(compressed_bytes_of_NPY_array).
    The NPY header encodes shape and dtype, so fft_size is ignored.
    """
    if not os.path.exists(raw_filename):
        logging.error(f"Raw file not found: {raw_filename}")
        return None

    try:
        # Read compressed data
        with open(raw_filename, 'rb') as f:
            compressed_data = f.read()

        # Decompress the data
        decompressed_data = zlib.decompress(compressed_data)

        # Load NPY array from in-memory buffer
        arr = np.load(BytesIO(decompressed_data), allow_pickle=False)
        # Optional sanity log
        logging.debug(f"Loaded NPY raw data: shape={arr.shape}, dtype={arr.dtype}")
        return arr

    except zlib.error as e:
        logging.error(f"Failed to decompress raw data from {raw_filename}: {e}")
        return None
    except Exception as e:
        logging.error(f"Failed to load NPY raw data from {raw_filename}: {e}")
        return None


def write_raw(run: CaptureRun, data):
    """Write FFT data as compressed NPY (npy-inside-zlib) and log size/timing.

    Logs include:
    - Uncompressed NPY size (MB)
    - Compressed size (MB) and compression ratio
    - Array shape
    - Serialize / compress / write / total time (ms)
    """
    try:
        t_start = time.perf_counter()

        directory = create_dirname(run, subdirectory_raw)
        filename = create_filename_raw(run.counter, run.id)
        raw_filename = directory + filename

        # Ensure 2D int32 array
        data_array = np.asarray(data, dtype=np.int32)

        # Serialize to NPY in-memory
        buf = BytesIO()
        np.save(buf, data_array, allow_pickle=False)
        npy_bytes = buf.getvalue()
        t_after_serialize = time.perf_counter()

        # Compress
        compressed_data = zlib.compress(npy_bytes)
        t_after_compress = time.perf_counter()

        # Write to disk
        with open(raw_filename, 'wb') as f:
            f.write(compressed_data)
        t_after_write = time.perf_counter()

        # Metrics
        uncompressed_mb = len(npy_bytes) / (1024 * 1024)
        compressed_mb = len(compressed_data) / (1024 * 1024)
        ratio = (compressed_mb / uncompressed_mb * 100.0) if uncompressed_mb > 0 else 0.0

        serialize_ms = (t_after_serialize - t_start) * 1000.0
        compress_ms = (t_after_compress - t_after_serialize) * 1000.0
        write_ms = (t_after_write - t_after_compress) * 1000.0
        total_ms = (t_after_write - t_start) * 1000.0

        log_raw_write_perf(
            total_ms=total_ms,
            compressed_mb=compressed_mb,
            uncompressed_mb=uncompressed_mb,
            ratio_pct=ratio,
            compress_ms=compress_ms,
            shape=data_array.shape,
        )
        return raw_filename

    except Exception as e:
        logging.error(f"Failed to write raw data: {e}")
        return None


def crop_waterfall_spectrum(waterfall_array, center_frequency, span, crop_start_freq, crop_end_freq, run=None):
    """
    Crop waterfall spectrum data to show only a specific frequency range for zoomed plots.

    Args:
        waterfall_array: 2D array of spectrum data (time × frequency)
        center_frequency: Original center frequency (kHz)
        span: Original frequency span (kHz)
        crop_start_freq: Start frequency of desired crop (kHz)
        crop_end_freq: End frequency of desired crop (kHz)
        run: Optional run context for log collection

    Returns:
        tuple: (cropped_waterfall, actual_start_freq, actual_end_freq, start_bin, end_bin)
    """
    original_start_freq = center_frequency - span / 2
    original_end_freq = center_frequency + span / 2
    freq_per_bin = span / waterfall_array.shape[1]

    # Validate crop range is within original spectrum
    if crop_end_freq < original_start_freq or crop_start_freq > original_end_freq:
        raise ValueError(
            f"Crop range ({crop_start_freq:.1f}-{crop_end_freq:.1f} kHz) is outside original spectrum ({original_start_freq:.1f}-{original_end_freq:.1f} kHz)")

    if crop_start_freq >= crop_end_freq:
        raise ValueError(
            f"Invalid crop range: start ({crop_start_freq:.1f} kHz) must be < end ({crop_end_freq:.1f} kHz)")

    # Clamp crop range to available spectrum
    clamped_start_freq = max(crop_start_freq, original_start_freq)
    clamped_end_freq = min(crop_end_freq, original_end_freq)

    # Find corresponding bins
    start_bin = int(round((clamped_start_freq - original_start_freq) / freq_per_bin))
    end_bin = int(round((clamped_end_freq - original_start_freq) / freq_per_bin))

    # Ensure valid range
    start_bin = max(0, start_bin)
    end_bin = min(waterfall_array.shape[1], end_bin)

    if end_bin <= start_bin:
        raise ValueError(f"Invalid bin range: start_bin={start_bin}, end_bin={end_bin}")

    # Crop the waterfall spectrum (all time samples, frequency subset)
    cropped_waterfall = waterfall_array[:, start_bin:end_bin]

    # Calculate actual frequencies based on bin boundaries
    actual_start_freq = original_start_freq + (start_bin * freq_per_bin)
    actual_end_freq = original_start_freq + (end_bin * freq_per_bin)
    actual_span = actual_end_freq - actual_start_freq

    # Collect the cropping operation information
    reduction_pct = (1 - cropped_waterfall.shape[1] / waterfall_array.shape[1]) * 100

    if run is not None:
        try:
            from qrm_logger.data.log import collect_log_text as _collect
            _collect(run, 'load_and_crop_data', "Waterfall spectrum crop:")
            _collect(run, 'load_and_crop_data', f"  Requested: {crop_start_freq:.1f} - {crop_end_freq:.1f} kHz ({crop_end_freq - crop_start_freq:.1f} kHz span)")
            _collect(run, 'load_and_crop_data', f"  Actual: {actual_start_freq:.1f} - {actual_end_freq:.1f} kHz ({actual_span:.1f} kHz span)")
            _collect(run, 'load_and_crop_data', f"  Original: {original_start_freq:.1f} - {original_end_freq:.1f} kHz ({waterfall_array.shape[1]} bins)")
            _collect(run, 'load_and_crop_data', f"  Cropped: {actual_start_freq:.1f} - {actual_end_freq:.1f} kHz ({cropped_waterfall.shape[1]} bins)")
            _collect(run, 'load_and_crop_data', f"  Data reduction: {waterfall_array.shape[0]}×{waterfall_array.shape[1]} → {cropped_waterfall.shape[0]}×{cropped_waterfall.shape[1]} ({reduction_pct:.1f}% frequency reduction)")
            _collect(run, 'load_and_crop_data', f"  Resolution: {freq_per_bin*1000:.3f} Hz/bin")
        except Exception:
            pass

    return cropped_waterfall, actual_start_freq, actual_end_freq, start_bin, end_bin


def decimate_data(waterfall_array, decimation_factor=4, method='mean'):
    """
    Decimate frequency data for faster visualization with configurable averaging method.

    Args:
        waterfall_array: 2D array of spectrum data (time × frequency)
        decimation_factor: Averaging block size (default: 4 = 75% reduction)
        method: Decimation method (default: 'mean')
                'mean' = Regular averaging (smooths noise, natural look)
                'max'  = Peak-preserving (keeps strong narrowband signals)
                'sample' = Simple sampling (fastest, may miss signals)

    Returns:
        Decimated waterfall array with reduced frequency bins
    """
    if decimation_factor <= 1:
        return waterfall_array

    # Simple sampling method (fastest but can miss signals)
    if method == 'sample':
        decimated = waterfall_array[:, ::decimation_factor]
        method_name = "sampling"
    else:
        # Block-based methods (averaging or max)
        num_time_samples, num_freq_bins = waterfall_array.shape

        # Calculate output size (truncate to fit exact blocks)
        output_freq_bins = num_freq_bins // decimation_factor
        input_freq_bins_used = output_freq_bins * decimation_factor

        # Truncate input to fit exact blocks
        truncated_array = waterfall_array[:, :input_freq_bins_used]

        # Reshape for block processing: (time, output_bins, decimation_factor)
        reshaped = truncated_array.reshape(num_time_samples, output_freq_bins, decimation_factor)

        # Apply the chosen method
        if method == 'max':
            decimated = np.max(reshaped, axis=2)  # Preserves peaks
            method_name = "max-averaging"
        else:  # Default to mean
            decimated = np.mean(reshaped, axis=2)  # Regular averaging
            method_name = "mean-averaging"

    original_rows, original_cols = waterfall_array.shape
    dec_rows, dec_cols = decimated.shape
    original_points = original_rows * original_cols
    decimated_points = dec_rows * dec_cols
    reduction_pct = (1 - decimated_points / original_points) * 100

    logging.info(
        f"Data decimation ({method_name}): ({original_rows}×{original_cols}) → ({dec_rows}×{dec_cols}) ({reduction_pct:.1f}% reduction, factor={decimation_factor})")

    return decimated