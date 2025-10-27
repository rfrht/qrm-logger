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

from qrm_logger.config.output_directories import subdirectory_metadata
from qrm_logger.core.objects import CaptureRun
from qrm_logger.utils.util import create_filename, create_dirname, create_dirname_meta


def save_plot_metadata(run: CaptureRun, capture_params, plot_type):
    """Save plot metadata to CSV file for easier grid generation"""
    metadata_dir = create_dirname(run, subdirectory_metadata)

    metadata_file = metadata_dir + "/" + plot_type+ "_plots_metadata.csv"
    plot_filename = create_filename(run, plot_type, "png").lstrip("/")  # Remove leading slash

    # Check if file exists to determine if we need to write header
    file_exists = os.path.exists(metadata_file)

    with open(metadata_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header if file is new
        if not file_exists:
            writer.writerow(['count', 'time_string', 'position', 'capture_id', 'note', 'filename'])

        # Write metadata row
        time_string = run.time.strftime('%H:%M')

        # Extract values
        note = None
        if capture_params is not None:
            try:
                note = getattr(capture_params, 'note', None)
            except Exception:
                pass

        writer.writerow([
            str(run.counter).zfill(4),
            time_string,
            str(run.position).zfill(2),
            run.id,
            note or "",
            plot_filename
        ])

    logging.debug(f"Saved plot metadata: {plot_filename}")


def load_plot_metadata(capture_set_id, date_string, plot_type):
    """Load plot metadata from CSV file"""
    metadata_dir = create_dirname_meta (subdirectory_metadata , capture_set_id, date_string)
    metadata_file = metadata_dir + "/" + plot_type+ "_plots_metadata.csv"

    metadata = {}

    if not os.path.exists(metadata_file):
        logging.warning(f"Metadata file not found: {metadata_file}")
        return metadata

    with open(metadata_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['filename']
            metadata[filename] = {
                'count': row['count'],
                'capture_id': row['capture_id'],
                'note': row['note'],
                'position': row['position'],
                'time_string': row['time_string']
            }

    logging.debug(f"Loaded metadata for {len(metadata)} plots")
    return metadata

