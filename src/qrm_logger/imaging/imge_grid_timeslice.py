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
Time-slice grid utilities (across days) extracted from image_grid.
Provides:
- get_timeslice_grids(capture_set_id, plot_type)
- generate_time_slice_grid(capture_set_id, plot_type, anchor_hour)
"""

import logging
import os
import glob
from datetime import datetime, timedelta

from PIL import Image

from qrm_logger.config.output_directories import (
    output_directory,
    subdirectory_grids_full,
    subdirectory_grids_resized,
    subdirectory_metadata,
    subdirectory_plots_resized,
)
from qrm_logger.config.visualization import (
    grid_show_title_label,
    timeslice_days_back,
)
from qrm_logger.data.metadata import load_plot_metadata
from qrm_logger.utils.util import create_dirname_flat, check_file_path

# Reuse rendering helpers from the main image_grid module
from qrm_logger.imaging.image_grid import (
    image_grid,
    create_text_image,
    create_time_note_image,
    SPARSE_COLUMN_THRESHOLD,
)


def get_timeslice_grids(capture_set_id, plot_type):
    """List available time-slice grids (across days) by hour.
    Returns list of { hour, full, resized, last_updated }.
    """
    dir_full = create_dirname_flat(capture_set_id, subdirectory_grids_full)
    dir_resized = create_dirname_flat(capture_set_id, subdirectory_grids_resized)

    prefix = f"{capture_set_id}_{plot_type}_timeslice_H"

    entries = {}

    def _collect(dir_path, kind):
        files = glob.glob(os.path.join(dir_path, '*.png'))
        for f in files:
            base = os.path.basename(f)
            if not base.startswith(prefix):
                continue
            if kind == 'full' and not base.endswith('_full.png'):
                continue
            if kind == 'resized' and not base.endswith('_resized.png'):
                continue
            # Extract hour after _timeslice_H
            try:
                tail = base.split('_timeslice_H', 1)[1]
                hh = tail.split('_', 1)[0]
                hour = int(hh)
            except Exception:
                continue
            rel_path = os.path.relpath(f, output_directory).replace('\\', '/')
            e = entries.get(hour)
            if not e:
                e = { 'hour': hour, 'full': None, 'resized': None, 'last_updated': None }
                entries[hour] = e
            e[kind] = rel_path
            try:
                mtime = os.stat(f).st_mtime_ns
                if not e['last_updated'] or mtime > e['last_updated']:
                    e['last_updated'] = mtime
            except Exception:
                pass

    _collect(dir_full, 'full')
    _collect(dir_resized, 'resized')

    result = []
    for hour in sorted(entries.keys()):
        e = entries[hour]
        for k in ('full', 'resized'):
            if e[k]:
                e[k] = f"{e[k]}?t={e['last_updated']}"
        result.append(e)
    return result


def generate_time_slice_grid(capture_set_id, plot_type, anchor_hour):
    """Generate a grid comparing the same hour across multiple days.

    Saves two files in grids_full/grids_resized with names:
      <set>_<plot_type>_timeslice_H{HH}_full.png and _resized.png
    """
    # Once-per-hour guard: if the resized output exists and was written this wall-clock hour, skip
    try:
        directory_grids_full = create_dirname_flat(capture_set_id, subdirectory_grids_full, True)
        out_full = directory_grids_full + "/" + capture_set_id + f"_{plot_type}_timeslice_H{int(anchor_hour):02d}_full.png"
        check_file_path(out_full)
        now = datetime.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        if os.path.exists(out_full):
            mtime = datetime.fromtimestamp(os.stat(out_full).st_mtime)
            if hour_start <= mtime < hour_end:
                logging.info(f"Time-slice skip (once-per-hour): {capture_set_id}/{plot_type} H{int(anchor_hour):02d} already rendered this hour")
                return
    except Exception:
        pass

    # Discover day folders (YYYY-MM-DD) under metadata
    meta_root = os.path.join(output_directory, capture_set_id, subdirectory_metadata)
    if not os.path.exists(meta_root):
        logging.info(f"No metadata directory for set {capture_set_id}")
        return
    days = [d for d in os.listdir(meta_root) if os.path.isdir(os.path.join(meta_root, d))]
    # sort desc (newest first)
    days.sort(reverse=True)
    if timeslice_days_back and isinstance(timeslice_days_back, int) and timeslice_days_back > 0:
        days = days[:timeslice_days_back]

    # For each day, select the first image recorded in the target hour
    per_day = []  # list of { day, time, files_by_spec }
    union_specs = []
    spec_seen = set()

    anchor_hour_int = int(anchor_hour)

    for day in days:
        md = load_plot_metadata(capture_set_id, day, plot_type) or {}
        if not md:
            continue  # skip day entirely
        # collect candidates exactly matching the anchor hour
        candidates = []  # list of (minute, time_string)
        for filename, meta in md.items():
            ts = meta.get('time_string') or '00:00'
            try:
                h, m = ts.split(':', 1)
                if int(h) == anchor_hour_int:
                    candidates.append((int(m), ts))
            except Exception:
                continue
        if not candidates:
            continue  # skip day entirely
        # pick earliest minute within the hour
        candidates.sort(key=lambda x: x[0])
        chosen_time = candidates[0][1]
        files = {}
        for filename, meta in md.items():
            if meta.get('time_string') == chosen_time:
                spec_id = meta.get('capture_id')
                if spec_id and spec_id not in files:
                    files[spec_id] = filename
                    if spec_id not in spec_seen:
                        spec_seen.add(spec_id)
                        union_specs.append(spec_id)
        per_day.append({ 'day': day, 'time': chosen_time, 'files': files })

    if not union_specs:
        logging.info("Time-slice: no images found to compose")
        return

    # pick a sample image size from first available plot
    sample_w, sample_h = 512, 512
    for row in per_day:
        if row['files']:
            any_spec = next(iter(row['files'].keys()))
            img_path = os.path.join(output_directory, capture_set_id, subdirectory_plots_resized, row['day'], row['files'][any_spec])
            try:
                with Image.open(img_path) as im:
                    sample_w, sample_h = im.size
                    break
            except Exception:
                pass

    # Determine column widths using the actual image width (ensures time column images are sized to full cell height)
    row_count = len(per_day) + 1
    col_count_total = len(union_specs) + 1
    data_columns = col_count_total - 1
    def compute_column_widths(image_width):
        if data_columns <= SPARSE_COLUMN_THRESHOLD:
            time_w = int(image_width * 0.6)
            data_w = image_width
            return [time_w] + [data_w] * data_columns
        else:
            return None
    col_widths = compute_column_widths(sample_w)
    time_image_size = (col_widths[0], sample_h) if col_widths else (sample_w, sample_h)
    data_image_size = (col_widths[1], sample_h) if col_widths else (sample_w, sample_h)

    # Build image list: header + rows (use sizes aligned with column widths to avoid black padding)
    images = []
    header_text = f"{int(anchor_hour):02d}:00" if grid_show_title_label else ""
    images.append(create_text_image(header_text, 60, time_image_size, 40))
    for label in union_specs:
        images.append(create_text_image(label, 60, data_image_size, 70))

    # Use smaller fonts for the time-slice row first column (date/time)
    # Scale relative to image height and clamp to conservative bounds to avoid overflow
    ts_time_font = max(40, min(80, int(sample_h * 0.12)))
    ts_note_font = max(28, min(55, int(sample_h * 0.08)))
    for row in per_day:
        time_label = row['time'] or ''
        images.append(create_time_note_image(row['day'], time_label, time_image_size, ts_time_font, ts_note_font))
        for spec in union_specs:
            if spec in row['files']:
                images.append(os.path.join(output_directory, capture_set_id, subdirectory_plots_resized, row['day'], row['files'][spec]))
            else:
                # Fill missing spec cells with a plain blank tile (no text)
                images.append(Image.new(mode="RGB", size=data_image_size, color='grey'))

    grid_img = image_grid(images, rows=row_count, cols=col_count_total, w=sample_w, h=sample_h, col_widths=col_widths)

    # Save
    directory_grids_full = create_dirname_flat(capture_set_id, subdirectory_grids_full, True)
    filename_full = directory_grids_full + "/" + capture_set_id + f"_{plot_type}_timeslice_H{int(anchor_hour):02d}_full.png"
    check_file_path(filename_full)
    logging.info("save time-slice grid file "+str(grid_img.size)+ ": "+ filename_full)
    grid_img.save(filename_full)

    directory_grids_resized = create_dirname_flat(capture_set_id, subdirectory_grids_resized, True)
    filename_resized = directory_grids_resized + "/" + capture_set_id + f"_{plot_type}_timeslice_H{int(anchor_hour):02d}_resized.png"
    check_file_path(filename_resized)
    grid_img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    logging.info("save time-slice resized grid file "+str(grid_img.size)+ ": "+ filename_resized)
    grid_img.save(filename_resized)
    grid_img.close()

