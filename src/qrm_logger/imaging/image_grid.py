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
Image grid generation for spectrum plot collections.
Combines multiple spectrum plots into time-series grids with configurable column layouts.
"""

import argparse
import glob
import logging
import os

from PIL import Image, ImageDraw

from qrm_logger.config.visualization import png_compression_level, grid_sort_latest_first, grid_max_rows, grid_time_window_hours, grid_show_title_label
from qrm_logger.config.output_directories import output_directory, subdirectory_grids_full, subdirectory_grids_resized, subdirectory_plots_resized
from qrm_logger.data.metadata import load_plot_metadata
from qrm_logger.utils.util import  create_dirname, create_dirname_flat, create_dirname_meta

# Column layout threshold for sparse vs dense grid optimization
SPARSE_COLUMN_THRESHOLD = 5


def image_grid(imgs, rows, cols, w, h, col_widths=None):
    """Create image grid with support for variable column widths
    
    Args:
        imgs: List of images
        rows: Number of rows
        cols: Number of columns
        w: Default width for images
        h: Height for images (consistent across all)
        col_widths: List of widths for each column (None = use default width for all)
    """
    if col_widths is None:
        col_widths = [w] * cols
    
    total_width = sum(col_widths)
    grid = Image.new('RGB', size=(total_width, rows * h))
    
    for i, img in enumerate(imgs):
        row = i // cols
        col = i % cols
        
        # Calculate x position based on cumulative column widths
        x_pos = sum(col_widths[:col])
        y_pos = row * h

        # image_path
        if isinstance(img, str):
            img = Image.open(img)
        
        # Resize image to fit column width while maintaining aspect ratio
        if img.size[0] != col_widths[col]:
            # Calculate new height maintaining aspect ratio
            aspect_ratio = img.size[1] / img.size[0]
            new_height = int(col_widths[col] * aspect_ratio)
            img_resized = img.resize((col_widths[col], min(new_height, h)), Image.Resampling.LANCZOS)
        else:
            img_resized = img
            
        grid.paste(img_resized, box=(x_pos, y_pos))
    
    return grid


def create_text_image(text, padding_top, image_size, font_size):
    im = Image.new(mode="RGB", size=image_size, color='grey')
    draw = ImageDraw.Draw(im)
    w = draw.textlength(text=text, font_size=font_size)
    h = font_size
    W = image_size[0]
    H = image_size[1]
    xpos = (W - w) / 2
    ypos = padding_top
    draw.text((xpos, ypos), text, (0, 0, 0), font_size=font_size, align="center")
    return im


def create_time_note_image(time_text, note_text, image_size, time_font_size, note_font_size=50):
    """Create an image with time at the top and note below it
    
    Args:
        time_text: Text to display for time
        note_text: Text to display for note
        image_size: Tuple of (width, height) for the image
        time_font_size: Font size for the time text
        note_font_size: Font size for the note text (default: 50)
    """
    im = Image.new(mode="RGB", size=image_size, color='grey')
    draw = ImageDraw.Draw(im)

    W, H = image_size

    # Draw time text at the very top
    time_w = draw.textlength(text=time_text, font_size=time_font_size)
    time_xpos = (W - time_w) / 2
    time_ypos = 10  # Minimal top padding
    draw.text((time_xpos, time_ypos), time_text, (0, 0, 0), font_size=time_font_size, align="center")

    # Draw note text below time (if note exists)
    if note_text:
        note_ypos = time_ypos + time_font_size + 10  # Closer spacing

        # Truncate note if it's too long
        max_width = W - 20  # Leave some padding
        truncated_note = note_text
        note_w = draw.textlength(text=truncated_note, font_size=note_font_size)

        # Keep removing characters until it fits
        while note_w > max_width and len(truncated_note) > 0:
            truncated_note = truncated_note[:-1]
            note_w = draw.textlength(text=truncated_note, font_size=note_font_size)

        # Add ellipsis if truncated
        if len(truncated_note) < len(note_text):
            truncated_note = truncated_note.rstrip() + "..."

        # Draw the note centered like the time text
        note_xpos = (W - note_w) / 2  # Center align
        draw.text((note_xpos, note_ypos), truncated_note, (0, 0, 0), font_size=note_font_size, align="center")

    return im


class ImageKey:
    def __init__(self, name, position, number, time_string):
        self.name = name
        self.number = number
        self.position = position
        self.time_string = time_string



def _prepare_grid_data(capture_set_id, date_string, plot_type):
    """Load metadata, choose window, derive labels, and flatten rows to tokens.
    Returns a context dict or None on early-exit conditions.
    """
    directory_input = create_dirname_meta(subdirectory_plots_resized, capture_set_id, date_string)

    # Load metadata from CSV
    metadata = load_plot_metadata(capture_set_id, date_string, plot_type)
    if not metadata:
        logging.error("No metadata found, cannot generate grid")
        return None

    # Utility helpers local to this function
    def parse_hour(time_str):
        try:
            return max(0, min(23, int(time_str.split(':', 1)[0])))
        except Exception:
            return 0

    def window_label(hour):
        start = (hour // grid_time_window_hours) * grid_time_window_hours
        end = min(24, start + grid_time_window_hours)
        return f"{start:02d}-{end:02d}", start, end

    # Build ImageKey list
    images_meta = []
    for filename, meta in metadata.items():
        images_meta.append(ImageKey(
            filename,
            meta['position'],
            meta['count'],
            meta['time_string']
        ))

    # Group images by recording number
    arr2 = {}
    for d in images_meta:
        t = arr2.setdefault(d.number, [])
        t.append(d)

    # Sort rows by number according to config
    sorted_arr2 = sorted(arr2.items(), key=lambda x: x[0], reverse=grid_sort_latest_first)

    # Apply optional max rows
    original_row_count = len(sorted_arr2)
    if grid_max_rows > 0 and len(sorted_arr2) > grid_max_rows:
        logging.info(f"Limiting grid to {grid_max_rows} most recent recordings (out of {original_row_count} total)")
        sorted_arr2 = sorted_arr2[:grid_max_rows]

    if not sorted_arr2:
        logging.warning("No rows found to build grid")
        return None

    # Determine target window from the most recent row
    latest_row = sorted_arr2[0][1]
    latest_hour = parse_hour(latest_row[0].time_string)
    label, start_h, end_h = window_label(latest_hour)

    # Filter rows that fall into this window
    rows = []
    for count_key, row_objs in sorted_arr2:
        hh = parse_hour(row_objs[0].time_string)
        if start_h <= hh < end_h:
            rows.append((count_key, row_objs))

    if not rows:
        logging.warning(f"No rows in window {label}, nothing to render")
        return None

    #logging.info(f"Current grid window: {label}h ({start_h:02d}-{end_h:02d})")

    # Collect all unique spec IDs from all rows in window (union approach)
    # This allows grid to handle added/removed specs gracefully
    all_spec_ids = []
    spec_id_set = set()
    for count_key, row_objs in rows:
        for obj in row_objs:
            spec_id = metadata[obj.name]['capture_id']
            if spec_id not in spec_id_set:
                all_spec_ids.append(spec_id)
                spec_id_set.add(spec_id)
    
    column_labels = all_spec_ids  # Use union of all specs as canonical columns
    col_count = len(column_labels)
    
    logging.info(f"Grid columns: {col_count} specs across {len(rows)} recordings")

    # Build flatarray with blank placeholders for missing specs
    flatarray = []
    for count_key, row_objs in rows:
        # Build map of available plots by spec_id for this recording
        available_plots = {}
        for obj in row_objs:
            spec_id = metadata[obj.name]['capture_id']
            available_plots[spec_id] = obj.name
        
        time_marker = "TIME" + row_objs[0].time_string
        flatarray.append(time_marker)
        
        # Add plots in canonical order, blank placeholder for missing specs
        for spec_id in column_labels:
            if spec_id in available_plots:
                flatarray.append(available_plots[spec_id])
            else:
                flatarray.append("BLANK")  # Missing spec placeholder

    if not flatarray:
        logging.warning(f"No valid content to render for window {label}")
        return None

    # Pre-build lookup table for notes by count (O(1))
    notes_by_count = {}
    for _, meta in metadata.items():
        ckey = meta['count']
        if ckey not in notes_by_count:
            notes_by_count[ckey] = meta['note'] if meta['note'] else ""

    return dict(
        directory_input=directory_input,
        metadata=metadata,
        rows=rows,
        label=label,
        column_labels=column_labels,
        flatarray=flatarray,
        notes_by_count=notes_by_count,
    )


def _decide_layout(data_columns, default_image_size=(512, 512)):
    """Compute placeholder image sizes and fonts based on column count."""
    # Local utility: width policy
    def compute_column_widths(image_width):
        if data_columns <= SPARSE_COLUMN_THRESHOLD:
            time_w = int(image_width * 0.6)
            data_w = image_width
            return [time_w] + [data_w] * data_columns
        else:
            return None

    # Local utility: font policy
    def compute_font_sizes():
        if data_columns <= SPARSE_COLUMN_THRESHOLD:
            return dict(date=50, time=80, note=35, freq=80)
        else:
            return dict(date=80, time=120, note=50, freq=80)

    # Placeholder sizes for header/body image generation
    col_widths = compute_column_widths(default_image_size[0])
    if col_widths:
        time_image_size = (col_widths[0], default_image_size[1])
        data_image_size = (col_widths[1], default_image_size[1])
    else:
        time_image_size = default_image_size
        data_image_size = default_image_size

    fonts = compute_font_sizes()
    return dict(time_image_size=time_image_size, data_image_size=data_image_size, fonts=fonts)


def _render_and_save(ctx, layout, capture_set_id, date_string, plot_type):
    images = []

    # Header images
    header_text = f"{date_string}" if grid_show_title_label else ""
    images.append(create_text_image(header_text, 80, layout['time_image_size'], layout['fonts']['date']))
    for label in ctx['column_labels']:
        images.append(create_text_image(label, 80, layout['data_image_size'], layout['fonts']['freq']))

    # Body images
    current_row_index = 0
    for token in ctx['flatarray']:
        if token.startswith("TIME"):
            tname = token.lstrip("TIME")
            row_counter = ctx['rows'][current_row_index][0]
            current_row_index += 1
            count_key = str(row_counter).zfill(4)
            note_text = ctx['notes_by_count'].get(count_key, "")
            time_note_image = create_time_note_image(
                tname, note_text, layout['time_image_size'], layout['fonts']['time'], layout['fonts']['note']
            )
            images.append(time_note_image)
        elif token == "BLANK":
            # Create blank placeholder for spec that didn't exist in this recording
            blank_img = create_text_image(
                "Not Recorded",
                layout['data_image_size'][1] // 2,
                layout['data_image_size'],
                40
            )
            images.append(blank_img)
        else:
            filename = token
            image_path = ctx['directory_input'] + filename
            if os.path.exists(image_path):
                images.append(image_path)
            else:
                logging.warning(f"Image file not found: {filename}, creating blank placeholder")
                images.append(create_text_image("Missing Image", 50, layout['data_image_size'], 30))

    # Grid sizing
    row_count = current_row_index + 1  # +1 for header row
    col_count_total = len(ctx['column_labels']) + 1  # +1 time column

    # use the image size of the first image in the grid
    size_image = Image.open(images[col_count_total + 1])
    w, h = size_image.size
    size_image.close()

    logging.info(f"generate grid: {row_count} rows, {col_count_total} columns for window {ctx['label']}")

    # Final column widths using actual image width
    data_columns = col_count_total - 1
    def compute_column_widths(image_width):
        if data_columns <= SPARSE_COLUMN_THRESHOLD:
            time_w = int(image_width * 0.6)
            data_w = image_width
            return [time_w] + [data_w] * data_columns
        else:
            return None
    col_widths = compute_column_widths(w)

    grid = image_grid(images, rows=row_count, cols=col_count_total, w=w, h=h, col_widths=col_widths)

    # Save images
    directory_grids_full = create_dirname_flat(capture_set_id, subdirectory_grids_full)
    filename_full = directory_grids_full + capture_set_id + f"_{plot_type}_grid_{date_string}_[{ctx['label']}]_full.png"
    logging.info("save grid file "+str(grid.size)+ ": "+ filename_full)
    grid.save(filename_full)

    grid_resized_size = (2048, 2048) if row_count < 50 else (4096, 4096)

    directory_grids_resized = create_dirname_flat(capture_set_id, subdirectory_grids_resized)
    filename_resized = directory_grids_resized + capture_set_id + f"_{plot_type}_grid_{date_string}_[{ctx['label']}]_resized.png"

    grid.thumbnail(grid_resized_size, Image.Resampling.LANCZOS)
    logging.info("save resized grid file "+str(grid.size)+ ": "+ filename_resized)

    grid.save(filename_resized)
    grid.close()


def generateGrid(capture_set_id, date_string, plot_type):
    ctx = _prepare_grid_data(capture_set_id, date_string, plot_type)
    if not ctx:
        return

    layout = _decide_layout(len(ctx['column_labels']), default_image_size=(512, 512))

    _render_and_save(ctx, layout, capture_set_id, date_string, plot_type)

    #logging.info("grid done")

def get_grids(capture_set_id, plot_type):
    from qrm_logger.config.output_directories import output_directory
    import os

    dir_full = create_dirname_flat(capture_set_id, subdirectory_grids_full)
    dir_resized = create_dirname_flat(capture_set_id, subdirectory_grids_resized)
    #date_prefix = "_grid_"
    date_prefix = "_" + plot_type + "_grid_"

    # Collect entries per (date, label)
    parts_map = {}

    def collect(dir_path, kind, suffix):
        files = glob.glob(dir_path + "/*.png")
        for f in files:
            base = os.path.basename(f)
            if not base.endswith(suffix):
                continue
            # Ensure expected prefix exists and tail is long enough
            name_parts = base.split(date_prefix, 1)
            if len(name_parts) < 2:
                continue
            tail = name_parts[1]  # expected: {date}_[{label}]_suffix
            if len(tail) < len(suffix):
                continue
            # Strip suffix to get {date}_[{label}]
            core = tail[:-len(suffix)]
            # Extract bracketed label at end
            lb = core.rfind('[')
            rb = core.rfind(']')
            if lb == -1 or rb == -1 or rb < lb:
                continue
            label = core[lb+1:rb]
            date_string = core[:lb]
            if date_string.endswith('_'):
                date_string = date_string[:-1]

            # Convert full path to relative path for the web UI
            relative_path = os.path.relpath(f, output_directory).replace("\\", "/")

            key = (date_string, label)
            entry = parts_map.get(key)
            if not entry:
                entry = {
                    "date": date_string,
                    "label": label,
                    "full": None,
                    "resized": None,
                    "full_size": None,
                    "resized_size": None
                }
                parts_map[key] = entry

            entry[kind] = relative_path
            try:
                size_bytes = os.path.getsize(f)
                if kind == "full":
                    entry["full_size"] = size_bytes
                else:
                    entry["resized_size"] = size_bytes
            except Exception as e:
                logging.warning(f"Could not read file size for {f}: {e}")

    collect(dir_full, "full", "_full.png")
    collect(dir_resized, "resized", "_resized.png")

    elems = list(parts_map.values())
    # Sort by date descending, then label descending (latest window first)
    elems.sort(key=lambda x: (x["date"], x["label"]), reverse=True)

    # Append cache-busting parameter ONLY to the latest window (first element)
    if len(elems) > 0:
        latest = elems[0]
        for key in ("full", "resized"):
            rel_path = latest.get(key)
            if not rel_path:
                continue
            abs_path = os.path.join(output_directory, rel_path.replace("/", os.sep))
            try:
                mtime_ns = os.stat(abs_path).st_mtime_ns
                latest[key] = f"{rel_path}?t={mtime_ns}"
            except Exception as ex:
                logging.warning(f"Could not append cache-busting parameter for {key}: {ex}")

    return elems


if __name__ == '__main__':
    #setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("-id", "--capture-set-id", type=str, required=True)
    parser.add_argument("-d", "--date-string", type=str, required=True)
    args = parser.parse_args()

    generateGrid(args.capture_set_id, args.date_string, "waterfall")
