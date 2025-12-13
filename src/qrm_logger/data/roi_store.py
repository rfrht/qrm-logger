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
Runtime-editable Regions of Interest (ROI) store.

- JSON-backed load/save for ROI configuration
- Structure: { "processing_enabled": bool, "rois": [ ... ] }
- Minimal validation only
"""

import json
import logging
import os
from typing import Any, Dict, List

from qrm_logger.core.objects import RecordingStatus, FreqRange, CaptureSpec, CaptureRun
from qrm_logger.execution.data_exporter import process_spectrum_data, process_grids
from qrm_logger.data.rms import write_rms

# JSON file path for ROI configuration (app root)
ROI_FILE_PATH = "config-roi.json"

# Required fields for every ROI definition
_REQUIRED_KEYS = {
    "roi_id",
    "base_capture_set_id",
    "capture_spec_id",
    "center_khz",
    "span_khz",
}


def generate_default_roi_config():
    """Generate default config-roi.json from template if it doesn't exist."""
    if os.path.exists(ROI_FILE_PATH):
        return
    
    from qrm_logger.config.roi_defaults import DEFAULT_ROI_JSON
    try:
        with open(ROI_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_ROI_JSON)
        logging.info(f"Generated default {ROI_FILE_PATH}")
    except Exception as e:
        logging.error(f"Failed to generate default ROI config: {e}")


def load_roi_config() -> Dict[str, Any]:
    """Load ROI configuration from JSON.
    Returns { processing_enabled: bool, rois: list }.
    If file is missing, returns defaults { False, [] }.
    """
    try:
        if not os.path.exists(ROI_FILE_PATH):
            return { "processing_enabled": False, "rois": [] }
        with open(ROI_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logging.error("Invalid ROI file format; expected object with processing_enabled and rois")
            return { "processing_enabled": False, "rois": [] }
        pe = bool(data.get("processing_enabled", False))
        rois = data.get("rois", [])
        if not isinstance(rois, list):
            rois = []
        # Minimal validation per entry
        validated: List[Dict[str, Any]] = []
        for e in rois:
            if not isinstance(e, dict):
                continue
            if not (_REQUIRED_KEYS <= set(e.keys())):
                continue
            try:
                float(e["center_khz"])  # type check
                float(e["span_khz"])    # type check
            except Exception:
                continue
            validated.append(e)
        return { "processing_enabled": pe, "rois": validated }
    except Exception as ex:
        logging.error(f"Failed to load ROI config: {ex}")
        return { "processing_enabled": False, "rois": [] }


def get_roi_specs() -> Dict[str, Dict[str, Any]]:
    """Get ROI specs grouped by ROI set ID (base_capture_set_id + '_ROI').
    
    Returns:
        Dictionary mapping ROI set IDs to objects with description and specs.
        Example: {
            "BANDS_ROI": {
                "description": "Custom ROI configuration",
                "specs": [
                    {"id": "7M-ROI", "freq": 7100, "span": 100, "freq_range": {...}},
                    ...
                ]
            }
        }
    """
    result = {}
    try:
        cfg = load_roi_config()
        if not cfg.get('processing_enabled', False):
            return result
        
        rois = cfg.get('rois', [])
        # Group ROIs by base_capture_set_id
        roi_by_base = {}
        for roi in rois:
            base_id = roi.get('base_capture_set_id')
            if not base_id:
                continue
            if base_id not in roi_by_base:
                roi_by_base[base_id] = []
            roi_by_base[base_id].append(roi)
        
        # Create ROI set entries
        for base_id, roi_list in roi_by_base.items():
            roi_set_id = f"{base_id}_ROI"
            roi_specs = []
            for idx, roi in enumerate(roi_list):
                try:
                    roi_id = str(roi.get('roi_id', '')).strip()
                    center_khz = float(roi.get('center_khz'))
                    span_khz = float(roi.get('span_khz'))
                    margin_khz = float(roi.get('margin_khz', 0))
                    
                    if not roi_id:
                        continue
                    
                    start_khz = center_khz - span_khz / 2.0
                    end_khz = center_khz + span_khz / 2.0
                    
                    roi_specs.append({
                        'spec_index': idx,
                        'id': roi_id,
                        'freq': center_khz,
                        'span': span_khz,
                        'freq_range': {
                            'freq_start': start_khz,
                            'freq_end': end_khz,
                            'margin': margin_khz
                        }
                    })
                except Exception:
                    continue
            
            if roi_specs:
                result[roi_set_id] = {
                    'description': f"Custom ROI configuration based on {base_id}",
                    'specs': roi_specs
                }
    except Exception as e:
        logging.error(f"Error getting ROI specs: {e}")
    
    return result


def save_roi_config(cfg: Dict[str, Any]) -> bool:
    """Save ROI configuration (full replacement).
    Expects an object with keys: processing_enabled (bool), rois (list).
    Performs minimal validation; writes JSON to disk.
    """
    import re
    
    if not isinstance(cfg, dict):
        raise ValueError("Body must be an object with 'processing_enabled' and 'rois'")

    pe = cfg.get("processing_enabled")
    rois = cfg.get("rois")
    if not isinstance(pe, bool):
        raise ValueError("'processing_enabled' must be a boolean")
    if not isinstance(rois, list):
        raise ValueError("'rois' must be an array")

    # ROI ID validation pattern: alphanumeric, underscore, dash, space
    roi_id_pattern = re.compile(r'^[a-zA-Z0-9_\- ]+$')

    # Minimal per-entry check (required keys and numeric fields)
    for i, e in enumerate(rois):
        if not isinstance(e, dict):
            raise ValueError("ROI entries must be objects")
        if not (_REQUIRED_KEYS <= set(e.keys())):
            raise ValueError("ROI entry missing required fields")
        
        # Validate ROI ID format
        roi_id = str(e.get("roi_id", "")).strip()
        if not roi_id:
            raise ValueError(f"ROI entry {i}: roi_id cannot be empty")
        if not roi_id_pattern.match(roi_id):
            raise ValueError(f"ROI entry {i}: roi_id '{roi_id}' contains invalid characters. Only alphanumeric, underscore, dash, and space are allowed.")
        if len(roi_id) > 50:
            raise ValueError(f"ROI entry {i}: roi_id '{roi_id}' is too long (max 50 characters)")
        
        try:
            float(e["center_khz"])  # noqa: F841
            float(e["span_khz"])    # noqa: F841
        except Exception:
            raise ValueError("center_khz and span_khz must be numbers")

    try:
        parent = os.path.dirname(os.path.abspath(ROI_FILE_PATH))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        with open(ROI_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump({"processing_enabled": pe, "rois": rois}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as ex:
        logging.error(f"Failed to save ROI config: {ex}")
        return False


def process_rois(capture_set, runs, status: RecordingStatus, capture_params):
    """Generate ROI plots after normal processing for a capture set.
    - Reads ROI definitions from ROI store
    - For each ROI matching this set, builds a virtual run that reuses the recorded raw data
    - Processes spectrum data and generates a separate ROI grid under <set>_ROI
    Skips RMS export for ROI sets.
    """
    try:
        cfg = load_roi_config()
    except Exception as e:
        logging.error(f"Failed to load ROI config: {e}")
        return

    if not cfg.get('processing_enabled', False):
        logging.info("ROI processing disabled; skipping")
        return

    rois = [r for r in cfg.get('rois', []) if r.get('base_capture_set_id') == capture_set.id]
    if not rois:
        return

    # Map source runs by their capture spec id (run.id)
    run_by_id = {r.id: r for r in runs if getattr(r, 'raw_filename', None)}

    roi_runs = []
    roi_set_id = f"{capture_set.id}_ROI"

    for idx, roi in enumerate(rois):
        try:
            roi_id = str(roi.get('roi_id', '')).strip()
            base_spec_id = str(roi.get('capture_spec_id', '')).strip()
            center_khz = float(roi.get('center_khz'))
            span_khz = float(roi.get('span_khz'))
            margin_khz = float(roi.get('margin_khz')) if roi.get('margin_khz') is not None else 0.0
        except Exception as e:
            logging.warning(f"Skipping ROI with invalid fields: {roi} ({e})")
            continue

        if not roi_id or not base_spec_id:
            logging.warning(f"Skipping ROI with missing ids: {roi}")
            continue

        source_run = run_by_id.get(base_spec_id)
        if not source_run:
            logging.warning(f"ROI '{roi_id}': source spec id '{base_spec_id}' not found in this batch; skipping")
            continue
        if not getattr(source_run, 'raw_filename', None):
            logging.warning(f"ROI '{roi_id}': source run missing raw file; skipping")
            continue

        # Build a FreqRange for cropping
        start_khz = center_khz - span_khz / 2.0
        end_khz = center_khz + span_khz / 2.0
        freq_range = FreqRange(id=roi_id, freq_start=start_khz, freq_end=end_khz, crop_margin_khz=margin_khz)

        # Build a spec with ROI freq_range (freq/span in kHz)
        roi_spec = CaptureSpec(spec_index=idx, id=roi_id, freq=center_khz, span=span_khz, freq_range=freq_range)

        # Create a virtual run tied to ROI set, reuse source recording params
        rr = CaptureRun(
            id=roi_id,
            freq=source_run.freq,
            span=source_run.span,
            position=idx,
            counter=source_run.counter,
            capture_set_id=roi_set_id,
            date_string=source_run.date_string,
            fft_size=source_run.fft_size,
            rec_time_ms=capture_params.rec_time_sec * 1000,
            time=source_run.time,
            spec=roi_spec,
        )
        # Copy the actual capture start time from source run
        rr.capture_start_time = source_run.capture_start_time
        # Attach ROI marker and raw file
        rr.roi_id = roi_id
        rr.raw_filename = source_run.raw_filename

        roi_runs.append(rr)

    if not roi_runs:
        return

    logging.info(f"Processing {len(roi_runs)} ROI runs for set {capture_set.id}")
    # Process ROI spectrum data (plots + metadata)
    results = process_spectrum_data(roi_runs, status, capture_params)

    if results:
        # Write RMS for ROI set as well (enabled)
        try:
            write_rms(roi_set_id, results,  capture_params)
        except Exception as e:
            logging.error(f"Error writing ROI RMS: {e}")

        # Generate grid for ROI set
        status.operation = "GRID (ROI)"
        try:
            process_grids(roi_set_id, results[0].run.date_string)
        except Exception as e:
            logging.error(f"Error generating ROI grid: {e}")

        from src.qrm_logger.execution.data_exporter import process_timeslice_grids
        process_timeslice_grids(roi_set_id, capture_params)

