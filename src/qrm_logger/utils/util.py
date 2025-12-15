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
Utility functions for file naming, directory creation, and logging setup.
Provides common helper functions used throughout the application.
"""

import logging
import os
import shutil
import re
from pathlib import Path

from qrm_logger.config.band_definitions import band_markers
from qrm_logger.core.objects import CaptureRun, CaptureSpec, FreqRange

from qrm_logger.config.output_directories import output_directory


VERSION = "0.1.5"


def create_filename(run: CaptureRun, prefix, file_extension):
    num = str(run.counter).zfill(4)
    pos = str(run.position).zfill(2)
    timestring = run.time.strftime('%H.%M')
    filename = "/" + prefix + "-" + pos + "-" + run.id + "-" + num + " [" + timestring + "]." + file_extension
    return filename


def create_filename_raw(counter, id):
    prefix = "fft"
    file_extension = "raw"
    num = str(counter).zfill(4)
    filename = "/" + prefix + "-" + id + "-" + num + "." + file_extension
    return filename


def create_dirname(run: CaptureRun, subdirectory, mkdirs:bool = False):
    dir = check_file_path(run.capture_set_id + "/" + subdirectory + "/" + run.date_string + "/")
    if mkdirs:
        os.makedirs(dir, exist_ok=True)
    return str(dir)


def create_dirname_meta(subdirectory, capture_set_id, date_string, mkdirs:bool = False):
    dir = check_file_path(capture_set_id + "/" + subdirectory + "/" + date_string + "/")
    if mkdirs:
        os.makedirs(dir, exist_ok=True)
    return str(dir)


def create_dirname_flat(capture_set_id, subdirectory, mkdirs:bool = False):
    dir = check_file_path(capture_set_id + "/" + subdirectory + "/")
    if mkdirs:
        os.makedirs(dir, exist_ok=True)
    return str(dir)

def check_file_path(filename_input):
    #logging.info("check_filename: "+str(filename_input))
    base_dir = Path(output_directory).resolve()
    filename = Path(filename_input)
    requested_path = base_dir / filename
    # Ensure path remains within base directory
    if not requested_path.resolve().is_relative_to(base_dir):
        logging.error("Invalid Path "+filename_input)
        raise Exception("Invalid Path")
    return requested_path

def create_step_specs(start_mhz, end_mhz, step_mhz, suffix, crop_to_step=False, crop_margin_khz=0):
    specs = []
    count = 0
    for i in range(start_mhz, end_mhz + 1, step_mhz):
        name = str(i).zfill(2) + suffix
        freq_khz = i * 1000

        if crop_to_step:
            # Construct a FreqRange centered at i MHz with width equal to the step size.
            # Units are kHz.
            half_step_khz = int(round(step_mhz * 1000 / 2))
            start_khz = freq_khz - half_step_khz
            end_khz = freq_khz + half_step_khz

            freq_range = FreqRange(
                id=str(i),
                freq_start=start_khz,
                freq_end=end_khz,
                crop_margin_khz=crop_margin_khz
            )

            specs.append(CaptureSpec(count, name, freq_khz, freq_range=freq_range))
        else:
            specs.append(CaptureSpec(count, name, freq_khz))

        count = count + 1
    return specs


def create_simple_spec(index, id, center_khz, span_khz):

    freq_range = FreqRange(
        id=id,
        freq_start=center_khz - (span_khz / 2),
        freq_end=center_khz + (span_khz / 2),
        crop_margin_khz=10
    )

    return  CaptureSpec(index, id, center_khz,  freq_range=freq_range)

def create_vhf_specs():

    id = "145 MHz"
    center_khz = 145_000  # CaptureSpec.freq uses kHz
    freq_range = FreqRange(
        id=id,
        freq_start=144_000,  # kHz
        freq_end=146_000,    # kHz
        crop_margin_khz=10
    )

    s = CaptureSpec(0, id, center_khz, freq_range=freq_range)
    return [s]


def create_uhf_specs():
    return [
        create_simple_spec( 0, id = "432 MHz", center_khz = 432_000, span_khz = 2_000),
        create_simple_spec(1, id="437 MHz", center_khz=437_000, span_khz=2_000),
        #create_simple_spec(2, id="439 MHz", center_khz=439_000, span_khz=2_000)
    ]

def create_band_specs(band_ids, suffix=""):
    """
    Create CaptureSpecs based on amateur radio band markers.
    
    Args:
        band_ids: List of band ID strings to create specs for (e.g., ["80m", "40m", "20m", "15m", "10m"])
        suffix: Optional suffix to append to band ID (deprecated, IDs should include suffix)
    
    Returns:
        List of CaptureSpec objects with center frequency set to band start frequency (in kHz),
        span omitted (uses default SDR bandwidth), and FreqRange object for spectrum cropping.
    
    Notes on units:
        - CaptureSpec.freq is stored in kHz (consistent with create_specs()).
        - Conversion to Hz is handled when creating CaptureRun objects.
        - FreqRange uses default 50 kHz crop margin for cropping.
    """
    specs = []
    count = 0
    
    for band_id in band_ids:
        # Find the band with matching ID
        band = None
        for b in band_markers:
            if b.id == band_id:
                band = b
                break
                
        if band is None:
#            logging.warning(f"Band ID '{band_id}' not found in band_markers, skipping")
            continue
        
        # Use band start frequency as center frequency (kHz)
        center_freq_khz = band.start
        
        # Create spec name using band ID (optionally append suffix)
        spec_name = f"{band_id}{suffix}" if suffix else band_id
        
        # Create FreqRange for spectrum cropping
        freq_range = FreqRange(
            id=band_id,
            freq_start=band.start,
            freq_end=band.end,
            crop_margin_khz=50  # Default 50 kHz margin
        )
        
        # Create CaptureSpec with center frequency in kHz
        # Omit span parameter so default SDR bandwidth will be used
        # Attach FreqRange object for cropping
        spec = CaptureSpec(
            spec_index=count,
            id=spec_name,
            freq=center_freq_khz,  # kHz (conversion to Hz happens in the capture executor)
            freq_range=freq_range  # FreqRange object for cropping
        )
        specs.append(spec)
        count += 1
    
    return specs


def print_capture_set(capture_set):
    """Print capture set configuration to console."""
    if capture_set is None:
        logging.info("No capture set configured")
        return
    
    logging.info(f"Set ID: {capture_set.id}")
    if capture_set.description:
        logging.info(f"  Description: {capture_set.description}")
    
    for i, spec in enumerate(capture_set.specs):
        # Build the spec line: ID in quotes, freq range (without margin), center freq, span, margin
        parts = [f"  {i+1:2d}. \"{spec.id}\""]
        
        # Add freq range (excluding margin) if available
        if spec.freq_range:
            range_start = spec.freq_range.freq_start
            range_end = spec.freq_range.freq_end
            parts.append(f"range: {range_start}-{range_end} kHz")
        
        # Add center frequency in kHz
        parts.append(f"center: {spec.freq} kHz")
        
        # Add span if present
        if spec.span:
            parts.append(f"span: {spec.span} kHz")
        
        # Add margin if present
        if spec.freq_range and spec.freq_range.crop_margin_khz > 0:
            parts.append(f"margin: {spec.freq_range.crop_margin_khz} kHz")
        
        logging.info(", ".join(parts))


# Performance tracking
performance_times = []

def track_performance(operation_name, total_time):
    """Track and log performance statistics"""
    performance_times.append(total_time)
    if len(performance_times) > 50:  # Keep last 50 measurements
        performance_times.pop(0)
    
    # Log current and statistics
    if len(performance_times) > 1:
        min_time = min(performance_times)
        max_time = max(performance_times)
        avg_time = sum(performance_times) / len(performance_times)
        logging.info(f"{operation_name} timing - Total: {total_time:.2f}s | Stats: min={min_time:.2f}s, max={max_time:.2f}s, avg={avg_time:.2f}s (n={len(performance_times)})")
    else:
        logging.info(f"{operation_name} timing - Total: {total_time:.2f}s")


def nearest_existing_path(path: str) -> str:
    """Return the nearest existing ancestor for the given path.
    Useful when a configured directory does not yet exist, so disk usage can be queried on its parent.
    """
    p = os.path.abspath(path)
    while not os.path.exists(p):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return p


def free_disk_mb_for_path(path: str) -> int | None:
    """Fast cross-platform free disk space for the path's mount/drive, in MB.
    Uses shutil.disk_usage (GetDiskFreeSpaceEx on Windows, statvfs on POSIX).
    Returns None on failure.
    """
    try:
        base = nearest_existing_path(path)
        total, used, free = shutil.disk_usage(base)
        return int(free // (1024 * 1024))
    except Exception:
        return None


def check_config():
    """Validate configuration settings and capture set definitions."""
    from qrm_logger.config.recording_params import min_db, max_db
    from qrm_logger.config.capture_definitions import capture_sets
    
    # Basic dB sanity check
    if min_db > max_db:
        logging.error("min_db greater than max_db")
        quit()

    # Simple cross-platform filesystem safety check for CaptureSet IDs
    # Disallow characters invalid on Windows (and '/' for Linux)
    invalid_chars = '<>:"/\\|?*'

    for s in capture_sets:
        cs_id = getattr(s, 'id', None)
        if not isinstance(cs_id, str) or not cs_id:
            logging.error("Invalid CaptureSet id: must be a non-empty string")
            quit()
        if any(ch in invalid_chars for ch in cs_id):
            logging.error(f"Invalid CaptureSet id '{cs_id}': contains invalid filesystem characters")
            quit()


def check_capture_sets():
    """Validate all capture sets and their specs for problematic characters.

    Checks:
    - Capture set IDs and spec IDs should only contain alphanumeric, underscore, dash, and space
    - IDs should not be empty
    - IDs should not be excessively long
    - No duplicate capture set IDs
    - No duplicate spec IDs within a capture set

    Logs warnings for any issues found but does not raise exceptions.
    """
    # Pattern: alphanumeric, underscore, dash, space
    id_pattern = re.compile(r'^[a-zA-Z0-9_\- ]+$')

    set_ids_seen = set()
    issues = []

    from qrm_logger.config.capture_definitions import capture_sets

    for capture_set in capture_sets:
        # Validate capture set ID
        set_id = capture_set.id

        if not set_id or not isinstance(set_id, str):
            issues.append(f"Capture set has invalid or empty ID: {set_id}")
            continue

        if not id_pattern.match(set_id):
            issues.append(
                f"Capture set ID '{set_id}' contains invalid characters. Only alphanumeric, underscore, dash, and space are allowed.")

        if len(set_id) > 50:
            issues.append(f"Capture set ID '{set_id}' is too long (max 50 characters)")

        # Check for duplicate set IDs
        if set_id in set_ids_seen:
            issues.append(f"Duplicate capture set ID: '{set_id}'")
        set_ids_seen.add(set_id)

        # Validate specs within this set
        spec_ids_seen = set()

        if not hasattr(capture_set, 'specs') or not capture_set.specs:
            issues.append(f"Capture set '{set_id}' has no specs defined")
            continue

        for spec in capture_set.specs:
            spec_id = spec.id

            if not spec_id or not isinstance(spec_id, str):
                issues.append(f"Capture set '{set_id}': spec has invalid or empty ID: {spec_id}")
                continue

            if not id_pattern.match(spec_id):
                issues.append(
                    f"Capture set '{set_id}': spec ID '{spec_id}' contains invalid characters. Only alphanumeric, underscore, dash, and space are allowed.")

            if len(spec_id) > 50:
                issues.append(f"Capture set '{set_id}': spec ID '{spec_id}' is too long (max 50 characters)")

            # Check for duplicate spec IDs within this set
            if spec_id in spec_ids_seen:
                issues.append(f"Capture set '{set_id}': duplicate spec ID '{spec_id}'")
            spec_ids_seen.add(spec_id)

    # Log results
    if issues:
        logging.warning(f"Found {len(issues)} issue(s) in capture set configuration:")
        for issue in issues:
            logging.warning(f"  - {issue}")
    else:
        logging.info(f"Capture set validation passed: {len(capture_sets)} sets validated")

    return len(issues) == 0
