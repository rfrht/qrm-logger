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
import csv
from typing import List, Tuple

from qrm_logger.config.output_directories import subdirectory_log
from qrm_logger.core.objects import CaptureRun
from qrm_logger.utils.util import create_dirname_flat, check_file_path

# In-memory append-only buffer of collected messages (preserves insertion order)
# Each entry is ((capture_set_id, counter, run_id), type, message)
_LOG_BUFFER: List[Tuple[Tuple[str, int, str], str, str]] = []


def _key_for_run(run) -> Tuple[str, int, str]:
    try:
        cs = getattr(run, 'capture_set_id', '') or ''
        cnt = int(getattr(run, 'counter', 0) or 0)
        rid = str(getattr(run, 'id', '') or '')
        return (cs, cnt, rid)
    except Exception:
        return ('', 0, '')



def collect_log_text(run, type, message: str):
    """
    Collect a log message for the given run in an in-memory buffer.

    Args:
        run: CaptureRun-like object with capture_set_id, counter, id
        type: String indicating caller function name (e.g., 'calculate_rms')
        message: Text to record (may contain newlines)
    """
    if run is None or not message:
        return

    key = _key_for_run(run)

    global _LOG_BUFFER
    last_entry = _LOG_BUFFER[-1] if len(_LOG_BUFFER) > 0 else None

    if last_entry:
        del _LOG_BUFFER[-1]

    last_key, last_type, last_string = last_entry  if last_entry else (None, None, None)

    if last_entry and last_string and key == last_key and type == last_type:
        new_message = last_string + "\n" + message
        new_entry = (key, str(type), new_message)
    else:
        if last_entry:
            _LOG_BUFFER.append(last_entry)
        new_entry = (key, str(type), str(message))

    _LOG_BUFFER.append(new_entry)


def clear_collected_log_texts(run):
    """Clear any previously collected messages for the given run."""
    if run is None:
        return
    key = _key_for_run(run)
    global _LOG_BUFFER
    _LOG_BUFFER = [entry for entry in _LOG_BUFFER if entry[0] != key]


def clear_all_collected_log_texts():
    global _LOG_BUFFER
    _LOG_BUFFER = []


def write_log_text(run, recording_start_datetime):
    """
    Flush collected log messages for a run to CSV (log.csv) under the capture set's log subdirectory.

    The CSV schema:
      counter, date, time, id, type, log_text

    Args:
        run: CaptureRun-like object (must have capture_set_id, counter, id)
        recording_start_datetime: datetime to use for the 'date' and 'time' columns
    """
    global _LOG_BUFFER
    if run is None:
        logging.error("write_log_text called without a run context")
        return

    # Format date and time once using recording_start_datetime (batch time)
    try:
        date_string = recording_start_datetime.strftime('%Y-%m-%d') if recording_start_datetime else ''
        time_string = recording_start_datetime.strftime('%H:%M') if recording_start_datetime else ''
    except Exception:
        date_string = ''
        time_string = ''


    capture_set_id = getattr(run, 'capture_set_id', None)
    if not capture_set_id:
        logging.error("write_log_text: capture_set_id not found on run; aborting")
        return

    directory_log = create_dirname_flat(capture_set_id, subdirectory_log, True)
    csv_file = os.path.join(directory_log, "log_"+date_string+".csv")
    check_file_path(csv_file)

    header = "counter, date, time, id, type, log_text"

    # Write header only if file does not exist
    write_header = not os.path.exists(csv_file)
    if write_header:
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write('\n')



    # Fetch buffered messages for this run in insertion order
    key = _key_for_run(run)
    msgs: List[Tuple[str, str]] = [(type, text) for (k, type, text) in _LOG_BUFFER if k == key]

    if not msgs:
        return

    counter = getattr(run, 'counter', '')
    run_id = getattr(run, 'id', '')

    # Append a row for each message
    with open(csv_file, 'a', encoding='utf-8') as f:
        for type, text in msgs:
            text = text or ''
            type = type or ''
            # Sanitize to keep CSV structure intact
            safe_text = str(text).replace('\n', ' | ').replace(',', ';')
            safe_type = str(type).replace('\n', ' ').replace(',', ';')
            line = f"{counter}, {date_string}, {time_string}, {run_id}, {safe_type}, {safe_text}"
            f.write(line)
            f.write('\n')

    # Clear buffer entries for this run after a successful write (preserve order of others)
    _LOG_BUFFER = [entry for entry in _LOG_BUFFER if entry[0] != key]


def get_log_data_as_json(capture_set_id, days: int = 2):
    """
    Read daily log CSV files (log_YYYY-MM-DD.csv) and return JSON for the most recent N days.

    Args:
        capture_set_id: Identifier for the capture set whose logs to read.
        days (int, optional): Number of most recent day files to include. Defaults to 2.

    Returns:
        list: List of dictionaries representing each CSV row from the most recent `days` day files,
              or [] if no files found, or None if error
    """
    try:
        directory_log = create_dirname_flat(capture_set_id, subdirectory_log)
        if not os.path.isdir(directory_log):
            return []

        if not isinstance(days, int) or days <= 0:
            return []

        # Find daily log files named like log_YYYY-MM-DD.csv
        day_files = []  # list of tuples: (date_str, full_path)
        try:
            for name in os.listdir(directory_log):
                if not name.startswith("log_") or not name.endswith(".csv"):
                    continue
                date_part = name[4:-4]  # 'YYYY-MM-DD'
                # Quick validation of date format
                if (
                    isinstance(date_part, str)
                    and len(date_part) == 10
                    and date_part[4] == '-'
                    and date_part[7] == '-'
                    and date_part.replace('-', '').isdigit()
                ):
                    day_files.append((date_part, os.path.join(directory_log, name)))
        except Exception:
            # If listing fails for some reason, fall back to empty
            day_files = []

        if not day_files:
            return []

        # Sort by date string (ISO format sorts chronologically lexicographically)
        day_files.sort(key=lambda t: t[0])
        most_recent = day_files[-days:]

        json_data = []
        for _, csv_file_path in most_recent:
            if not os.path.exists(csv_file_path):
                continue
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    # Clean up keys and values (remove extra spaces, handle None values)
                    cleaned_row = {}
                    for key2, value in row.items():
                        clean_key = key2.strip() if key2 else ""
                        clean_value = value.strip() if value is not None else ""
                        # Convert pipe placeholder back to newlines for display
                        if clean_key == 'log_text' and clean_value:
                            # We wrote logs using ' | ' as a newline placeholder
                            clean_value = clean_value.replace(' | ', '\n')
                        cleaned_row[clean_key] = clean_value
                    json_data.append(cleaned_row)

        # Stable sort by counter descending; preserve within-counter creation order
        def _parse_counter(row):
            try:
                return int(str(row.get('counter', '')).strip())
            except Exception:
                return -1
        json_data_sorted = sorted(json_data, key=_parse_counter, reverse=True)

        return json_data_sorted

    except Exception as e:
        logging.error(f"Error reading log CSV file for {capture_set_id}: {e}")
        return None
