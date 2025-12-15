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
Data export functionality for FFT recordings.
Handles image generation, raw data storage, CSV metadata, and file compression.
"""

import logging
import traceback

import copy as _copy

import numpy as np
from timeit import default_timer as timer
from qrm_logger.data.analysis import calculate_rms
from qrm_logger.config.output_directories import subdirectory_plots_full, subdirectory_plots_resized
from qrm_logger.config.visualization import png_compression_level, skip_image_generation
from qrm_logger.core.config_manager import get_config_manager
from qrm_logger.data.metadata import save_plot_metadata
from qrm_logger.data.fft_data import load_and_crop_data
from qrm_logger.imaging.image_generator import generate_waterfall_plot, generate_average_spectrum_plot
from qrm_logger.core.objects import CaptureRun, ProcessingResult, RecordingStatus, CaptureParams
from qrm_logger.utils.util import create_dirname, create_filename, check_file_path
from qrm_logger.data.log import clear_collected_log_texts, write_log_text

from PIL import Image


def process_spectrum_data(runs, status: RecordingStatus, capture_params: CaptureParams):

    capture_set_id = runs[0].capture_set_id
    logging.info("processing spectrum data")

    status.operation =  "PLOT " + capture_set_id
    status.current_job_number = 0
    number = 0

    results = []
    for run in runs:
        if getattr(status, "cancel_requested", False):
            logging.info("Processing cancelled; aborting runs loop.")
            break
        try:
            logging.info("*" * 50)
            logging.info(run.id)
            t_run_start = timer()

            # Start of a new run: clear any previously collected messages for this run
            clear_collected_log_texts(run)

            data, data_cropped = load_and_crop_data(run)
            t_after_load = timer()
            # Handle error case where data loading failed
            if data is None:
                logging.error(f"Skipping processing for {run.id} due to data loading failure")
                # Still flush any collected error logs for this run
                write_log_text(run, capture_params.recording_start_datetime)
                continue
                
            raw_data = data_cropped if data_cropped is not None else data

            db_configs = _get_db_configurations(capture_params.is_calibration)
            for config_num, (min_db_val, max_db_val, db_name) in enumerate(db_configs, 0):
                if getattr(status, "cancel_requested", False):
                    break
                run_for_processing = run
                if capture_params.is_calibration:
                    capture_params.note = f"calib [{db_name}]"
                    if config_num > 0:
                        run_for_processing = _copy.deepcopy(run)
                        run_for_processing.counter = run_for_processing.counter + config_num

                capture_params.min_db_val = min_db_val
                capture_params.max_db_val = max_db_val

                gs = process(run_for_processing, raw_data, capture_params)

                if gs is not None:
                    results.append(gs)
            # Per-run performance summary
            try:
                t_run_end = timer()
                load_crop_s = t_after_load - t_run_start
                process_s = t_run_end - t_after_load
                total_s = t_run_end - t_run_start
                logging.info(
                    f"Perf: run {run.capture_set_id}/{run.id} total={total_s:.2f}s load+crop={load_crop_s:.2f}s process={process_s:.2f}s")
            except Exception:
                pass

            # Flush collected logs for this run after processing completes
            try:
                write_log_text(run, capture_params.recording_start_datetime)
            except Exception:
                pass

            number = number + 1
            status.current_job_number = number


        except Exception as e:
            logging.error(traceback.format_exc())
    return results

def _get_db_configurations(is_calibration):
    """Get dB configurations based on calibration mode."""
    config_manager = get_config_manager()
    base_min_db = config_manager.get("min_db")
    base_max_db = config_manager.get("max_db")

    if is_calibration:
        logging.info("CALIBRATION MODE: Processing with multiple dB ranges")
        db_configs = [
            (base_min_db, base_max_db, "+0 dB"),  # Original config
            (base_min_db - 12, base_max_db - 12, "-12 dB"),
            (base_min_db - 6, base_max_db - 6, "-6 dB"),
            (base_min_db - 3, base_max_db - 3, "-3 dB"),
            (base_min_db + 3, base_max_db + 3, "+3 dB"),
            (base_min_db + 6, base_max_db + 6, "+6 dB"),
            (base_min_db + 12, base_max_db + 12, "+12 dB"),
        ]
    else:
        db_configs = [(base_min_db, base_max_db, "")]  # Single configuration

    return db_configs


def process(run: CaptureRun, data, capture_params):
    """

    Args:
        run: CaptureRun containing processing parameters
        data: Pre-loaded FFT data array (numpy 2D array)
        capture_params: Optional parameters including note
        
    Returns:
        ProcessingResult with RMS analysis results
    """

    
    # Validate input data
    if data is None:
        logging.error(f"No data provided for processing run {run.id}")
        return None


    min_db_val = capture_params.min_db_val
    max_db_val = capture_params.max_db_val

    # Perform RMS calculation (avg_wf, center_frequency, and span calculated internally)
    rms_normalized, include_mask, rms_truncated = calculate_rms(run, data, min_db_val, max_db_val)
    
    # High-level RMS log lines
    #collect_log_text(run, 'process', f"Calculating RMS analysis for {run.id}")
    #collect_log_text(run, 'process', f"Using dB range: [{min_db_val}, {max_db_val}] (range: {max_db_val - min_db_val} dB)")

    # Create result object
    result = ProcessingResult()
    result.run = run
    result.rms_normalized = rms_normalized
    result.rms_truncated = rms_truncated
    
    # Handle image generation and related post-processing
    if not skip_image_generation:
#        logging.info(f"Generating images for {run.id}")

        generate_images(run, data,  min_db_val, max_db_val, "waterfall")
        generate_images(run, data,  min_db_val, max_db_val, "average")

        # Save plot metadata for grid generation
        save_plot_metadata(run, capture_params, "waterfall")
        save_plot_metadata(run, capture_params, "average")
    else:
        logging.info(f"Skipping image generation for {run.id} (disabled in config)")
    
    return result


def generate_images(run: CaptureRun, data, min_db_val, max_db_val, plot_type):
    """
    Generate spectrum plot images with pre-calculated RMS value.
    
    Args:
        run: CaptureRun containing plot parameters
        data: Pre-loaded FFT data array (numpy 2D array)
        min_db_val: Min dB value for spectrum scaling (required)
        max_db_val: Max dB value for spectrum scaling (required)

    """

    directory_plot = create_dirname(run, subdirectory_plots_full, True)

    file_extension = "png"
    prefix = plot_type
    plot_filename = create_filename(run, prefix, file_extension)
    plot_file = directory_plot + plot_filename
    check_file_path(plot_file)
    
    # Decimation is now handled inside generate_plot() using config values
    if plot_type == "waterfall":
        save_time_plot = generate_waterfall_plot(run, data, plot_file, min_db_val, max_db_val)
    elif plot_type == "average":
        save_time_plot = generate_average_spectrum_plot(run, data, plot_file, min_db_val, max_db_val)
    else:
        logging.error("invalid plot type: "+ plot_type)
        return

    directory_resized = create_dirname(run, subdirectory_plots_resized, True)
    filename_resized = directory_resized + plot_filename
    check_file_path(filename_resized)

    logging.debug("write resized " + filename_resized)

    size = 512, 512
    from timeit import default_timer as timer
    t_thumb_start = timer()
    i = Image.open(plot_file)
    i.thumbnail(size, Image.Resampling.LANCZOS)
    i.save(filename_resized, compress_level=png_compression_level)
    i.close()
    t_thumb_end = timer()

    # Log combined save time (plot save + thumbnail)
    try:
        save_total = (save_time_plot or 0.0) + (t_thumb_end - t_thumb_start)
        logging.info(f"Perf: save {run.capture_set_id}/{run.id} save_total={save_total:.2f}s")
    except Exception:
        pass



def process_grids(capture_set_id, date_string):
    """
    Finalize processing after all plots in a batch are completed.
    
    This function handles grid generation based on the configured update frequency.
    Should be called once after all runs in a recording batch have been processed.
    
    Args:
        capture_set_id: Capture set identifier
        date_string: Date string in YYYY-MM-DD format  

    """
    if skip_image_generation:
        logging.info("Skipping grid generation (image generation is disabled)")
        return
    
    #logging.info("Generating grids after batch completion")
    from qrm_logger.imaging.image_grid import generateGrid

    try:
        generateGrid(capture_set_id, date_string, "waterfall")
        generateGrid(capture_set_id, date_string, "average")
    except Exception as e:
        logging.error(f"Error generating grid: {e}")


def process_timeslice_grids(capture_set_id, capture_params):
    # Generate time-slice grids (across days) if enabled and this hour is configured
    try:
        from qrm_logger.core.config_manager import get_config_manager
        cfg = get_config_manager()
        if cfg.get("timeslice_autogenerate", False):
            hours = cfg.get("timeslice_hours", []) or []
            try:
                anchor_hour = int(capture_params.recording_start_datetime.strftime('%H'))
            except Exception:
                anchor_hour = None
            if anchor_hour is not None and anchor_hour in hours:
                logging.info("#" * 50)
                from qrm_logger.imaging.imge_grid_timeslice import generate_time_slice_grid
                for plot_type in ("waterfall", "average"):
                    generate_time_slice_grid(capture_set_id, plot_type, anchor_hour)
    except Exception as e:
        logging.error(f"Time-slice grid generation failed: {e}")