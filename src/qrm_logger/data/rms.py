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

import csv
import logging
import os
import shutil
import tempfile

from qrm_logger.config.output_directories import subdirectory_csv
from qrm_logger.utils.util import create_dirname_flat


def write_rms(capture_set_id, results, capture_params):
    """
    Write both standard and truncated RMS data to separate CSV files.

    Args:
        results: List of ProcessingResult objects
        capture_params: Optional CaptureParams to extract metadata (e.g., note)
    """
    # Extract data from results
    standard_rms = [result.rms_normalized for result in results]
    truncated_rms = [result.rms_truncated for result in results]
    capture_ids = [result.run.id for result in results]

    # Write standard RMS data (average calculated internally)
    write_csv(capture_set_id, standard_rms, capture_ids, capture_params, "rms_standard.csv")
    #logging.info("Written standard RMS data to rms_standard.csv")

    # Write truncated RMS data (average calculated internally)
    write_csv(capture_set_id, truncated_rms, capture_ids, capture_params, "rms_truncated.csv")
    #logging.info("Written truncated RMS data to rms_truncated.csv")


def _read_csv_spec_columns(csv_file):
    """
    Extract spec column names from CSV header.
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        List of spec column names (everything after 'avg' column)
    """
    if not os.path.exists(csv_file):
        return []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
            parts = [c.strip() for c in header.split(',')]
            # Extract spec columns (everything after 'avg')
            if 'avg' in parts:
                avg_idx = parts.index('avg')
                return parts[avg_idx + 1:]
    except Exception as e:
        logging.error(f"Failed to read CSV columns: {e}")
    
    return []


def _merge_spec_columns(existing_columns, current_spec_ids):
    """
    Merge existing and current spec columns.
    Preserves existing order and appends new specs at the end.
    
    Args:
        existing_columns: List of spec columns from CSV header
        current_spec_ids: List of spec IDs from current recording
        
    Returns:
        Tuple of (canonical_columns, columns_changed)
    """
    canonical_columns = existing_columns.copy()
    
    # Append new specs not in existing columns
    for spec_id in current_spec_ids:
        if spec_id not in canonical_columns:
            canonical_columns.append(spec_id)
    
    columns_changed = (canonical_columns != existing_columns)
    return canonical_columns, columns_changed


def _rewrite_csv_with_new_columns(csv_file, new_columns):
    """
    Rewrite existing CSV with updated column header.
    Preserves all data rows, filling new spec columns with -1.
    
    Args:
        csv_file: Path to CSV file
        new_columns: New list of spec columns
    """
    try:
        # Read existing data
        existing_data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Strip whitespace from keys, preserve values exactly (including empty strings)
                cleaned_row = {k.strip(): (v.strip() if v and v.strip() else '') for k, v in row.items()}
                existing_data.append(cleaned_row)
        
        # Write to temp file with new header
        temp_fd, temp_file = tempfile.mkstemp(suffix='.csv', text=True)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8', newline='') as f:
                # Write new header
                header = "counter, date, time, note, total, avg, " + ", ".join(new_columns)
                f.write(header + '\n')
                
                # Write data rows (preserve existing data, fill new spec columns with -1)
                for row in existing_data:
                    # Preserve all metadata fields exactly as they were
                    # Keys should already be stripped by cleaned_row processing
                    data_parts = [
                        row.get('counter', ''),
                        row.get('date', ''),
                        row.get('time', ''),
                        row.get('note', ''),
                        row.get('total', ''),
                        row.get('avg', '')
                    ]
                    
                    # Debug: Log if we're losing data
                    if row.get('counter') and not row.get('date'):
                        logging.warning(f"Row {row.get('counter')} missing date during CSV rewrite: {row}")
                    # Add spec values in new column order (-1 for new spec columns)
                    for col in new_columns:
                        data_parts.append(row.get(col, '-1'))
                    
                    f.write(", ".join(data_parts) + '\n')
            
            # Replace original with updated file
            shutil.move(temp_file, csv_file)
            logging.info(f"CSV rewritten with {len(new_columns)} columns")
            
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise
            
    except Exception as e:
        logging.error(f"Failed to rewrite CSV with new columns: {e}")
        raise


def write_csv(capture_set_id, rms_data, capture_ids, capture_params, filename="rms_output.csv"):
    """
    Write RMS results to CSV file with dynamic column handling.
    Automatically handles added/removed specs:
    - Reads existing columns from CSV header
    - Writes -1 for removed specs (preserves column positions)
    - Appends new specs to the end (extends header)
    - Rewrites CSV when columns change
    - Calculates total and average excluding removed specs (-1 values)

    Args:
        rms_data: List of RMS values to write
        capture_ids: List of run IDs corresponding to the RMS values
        capture_params: CaptureParams object to extract metadata (e.g., note)
        filename: Name of CSV file to write (default: "rms_output.csv")
    """
    counter = capture_params.counter
    recording_start_datetime = capture_params.recording_start_datetime
    directory_csv = create_dirname_flat(capture_set_id, subdirectory_csv)
    csv_file = directory_csv + "/" + filename
    
    # Step 1: Get existing columns from CSV header
    existing_columns = _read_csv_spec_columns(csv_file)
    
    # Step 2: Build current spec -> value mapping
    current_specs = {}
    for i, spec_id in enumerate(capture_ids):
        value = round(rms_data[i]) if rms_data[i] is not None else 0
        current_specs[spec_id] = value
    
    # Step 3: Merge columns (preserve order + append new)
    canonical_columns, columns_changed = _merge_spec_columns(existing_columns, capture_ids)
    
    # Log new specs
    for spec_id in canonical_columns:
        if spec_id not in existing_columns:
            logging.info(f"New spec added to {capture_set_id} CSV: {spec_id}")
    
    # Log removed specs (now receiving -1 values)
    for spec_id in existing_columns:
        if spec_id not in capture_ids:
            logging.info(f"Spec removed from {capture_set_id} recording (CSV column preserved with -1): {spec_id}")
    
    # Step 4: Build RMS row in canonical order (-1 for removed specs)
    rms_values = [current_specs.get(col, -1) for col in canonical_columns]
    
    # Calculate total and avg excluding removed specs (-1 values)
    # Note: This recalculates from the canonical rms_values (standard or truncated)
    # which correctly excludes removed specs from statistics
    active_values = [v for v in rms_values if v != -1]
    total = sum(active_values) if active_values else 0
    avg_value = round(total / len(active_values)) if active_values else 0
    
    # Step 5: Format metadata
    date_string = recording_start_datetime.strftime('%Y-%m-%d')
    time_string = recording_start_datetime.strftime('%H:%M')
    try:
        note = getattr(capture_params, 'note', None)
    except Exception:
        note = None
    safe_note = (note or "").replace("\n", " ").replace(",", ";")
    
    # Step 6: Handle header creation or update
    if columns_changed:
        if existing_columns:
            # Columns changed - rewrite entire CSV with new header
            logging.info(f"CSV columns changed for {capture_set_id}, rewriting file")
            _rewrite_csv_with_new_columns(csv_file, canonical_columns)
        else:
            # New file - write header
            header_line = "counter, date, time, note, total, avg, " + ", ".join(canonical_columns)
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(header_line + '\n')
    
    # Step 7: Append data row
    data_parts = [
        str(counter),
        date_string,
        time_string,
        safe_note,
        str(total),
        str(avg_value)
    ] + [str(v) for v in rms_values]
    
    with open(csv_file, 'a', encoding='utf-8') as f:
        f.write(", ".join(data_parts) + '\n')


def get_rms_data_as_json(capture_set_id, rms_type="standard"):
    """
    Read RMS CSV file and convert it to a structured format that preserves column order.

    Args:
        rms_type: Type of RMS data to retrieve. Options:
                 - "standard" (default): reads rms_standard_output.csv
                 - "truncated": reads rms_trunc_output.csv

    Returns:
        dict: Dictionary with 'headers' (list of column names) and 'rows' (list of row arrays)
              to guarantee column order preservation, or None if error
    """
    # Determine filename based on RMS type
    if rms_type == "truncated":
        filename = "rms_truncated.csv"
    elif rms_type == "standard":
        filename = "rms_standard.csv"
    else:
        logging.error(f"Invalid rms_type '{rms_type}'. Must be 'standard' or 'truncated'")
        return None

    directory_csv = create_dirname_flat(capture_set_id, subdirectory_csv)

    csv_file_path = f"{directory_csv}/{filename}"

    try:
        # Check if the file exists
        if not os.path.exists(csv_file_path):
            return {"headers": [], "rows": []}

        # Read the CSV file preserving exact column order
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            
            # Read header row
            header_row = next(csv_reader, None)
            if header_row is None:
                return {"headers": [], "rows": []}
            
            # Clean up header names (strip whitespace)
            headers = [h.strip() for h in header_row]
            
            # Read data rows as arrays
            rows = []
            for row in csv_reader:
                # Clean up values (strip whitespace)
                cleaned_row = [val.strip() if val else "" for val in row]
                rows.append(cleaned_row)

        # Sort data in reverse order (newest first)
        rows.reverse()

        return {"headers": headers, "rows": rows}

    except Exception as e:
        logging.error(f"Error reading {rms_type} RMS CSV file {csv_file_path}: {e}")
        return None

