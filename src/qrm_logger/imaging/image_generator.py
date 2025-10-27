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
Spectrum plot generation from FFT data.
Creates waterfall plots with frequency/time axes, band markers, and RMS calculations.
"""

import gc
import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator

from qrm_logger.core.config_manager import get_config_manager
from qrm_logger.config.visualization import draw_mhz_separators, draw_bandplan, png_compression_level, decimation_method
from qrm_logger.config.band_definitions import band_markers
from qrm_logger.core.objects import CaptureRun
from qrm_logger.data.fft_data import decimate_data
from qrm_logger.utils.util import track_performance

matplotlib.use('agg')
# Explicitly set Agg DPI to 100 (default)
matplotlib.rcParams['figure.dpi'] = 100


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n



def generate_average_spectrum_plot(run: CaptureRun, waterfall_array, filename, min_db_val=None, max_db_val=None):

    fill_color = "darkblue"
    plot_color = "yellow"

    from timeit import default_timer as timer
    total_start = timer()

    # Use effective (post-crop) parameters if available for display
    center_frequency = (getattr(run, 'freq_effective', run.freq)) / 1000
    span = (getattr(run, 'span_effective', run.span)) / 1000

    # Create figure early so we can query actual pixel width for decimation decision
    fig = plt.figure(figsize=(20, 8))

    fig_width_px = 1600  # Fallback if figure metrics unavailable (20in * 80 dpi)
    try:
        fig_width_px = int(fig.get_figwidth() * fig.get_dpi())
    except Exception:
        logging.warning("Could not determine figure metrics")
        pass

    waterfall_array = decimate_for_plot(waterfall_array, fig_width_px)

    start_freq = center_frequency - span / 2
    stop_freq = center_frequency + span / 2
    nbin = run.fft_size

    ax = plt.gca()
    ax.set_facecolor(fill_color)

    # Keep the x-axis identical to the waterfall view
    set_x_axis(center_frequency, span, waterfall_array, ax)

    # Prepare x coordinates (frequency bins) matching [:, 1:] columns
    num_cols = waterfall_array.shape[1] - 1
    # For a line plot, span the full domain [0, num_cols] so ticks from set_x_axis align without extra blank space
    x_coords = np.linspace(0, num_cols, num_cols)

    # Average the waterfall over the recording time (rows) to get a 1D spectrum
    # Note: first column is excluded (assumed metadata/index), consistent with prior usage
    if waterfall_array.shape[0] > 0 and num_cols > 0:
        avg_spectrum = np.nanmean(waterfall_array[:, 1:], axis=0)
    else:
        avg_spectrum = np.array([])

    # Determine y-axis limits
    if avg_spectrum.size > 0:
        # Use provided min/max if supplied; otherwise compute from the averaged spectrum
        y_min_base = min_db_val if min_db_val is not None else float(np.nanmin(avg_spectrum))
        y_max_base = max_db_val if max_db_val is not None else float(np.nanmax(avg_spectrum))
        y_min = y_min_base - 10
        y_max = y_max_base + 10
    else:
        # Fallback range if no data
        y_min, y_max = -120, 0

    # Plot the averaged spectrum as a regular matplotlib line plot
    plt.plot(x_coords, avg_spectrum, color=plot_color, linewidth=1.5)
    # Ensure x-axis matches the tick mapping (no default margins)
    ax.set_xlim(0, num_cols)
    ax.margins(x=0)

    # Apply y-axis scaling as requested
    ax.set_ylim(y_min, y_max)

    # Draw MHz separators and band markers using axis height (upper/lower thirds)
    pixel_ratio = num_cols / span if span != 0 else 0
    draw_lines(start_freq, stop_freq, pixel_ratio, ax)

    set_plot_title(run)

    from timeit import default_timer as timer
    start = timer()
    plt.savefig(filename,
                bbox_inches="tight",
                pad_inches=0.2,
                transparent=False,
                facecolor="grey",
                edgecolor='w',
                pil_kwargs={'compress_level': png_compression_level}
                )
    plt.close('all')
    gc.collect()
    end = timer()
    savefig_time = end - start
    total_time = end - total_start
    
    # Track performance statistics
    track_performance("Plot generation", total_time)

    # Return save time so caller can aggregate with thumbnail time
    return savefig_time


def generate_waterfall_plot(run: CaptureRun, waterfall_array, filename, min_db_val=None, max_db_val=None):
    """
    Generate spectrum plot with provided RMS value.

    Args:
        run: CaptureRun containing plot parameters
        waterfall_array: 2D array of spectrum data
        filename: Output plot filename
        rms_normalized: Pre-calculated RMS value (required)
        min_db_val: Min dB value for spectrum scaling (if None, uses config)
        max_db_val: Max dB value for spectrum scaling (if None, uses config)
    """
    from timeit import default_timer as timer
    total_start = timer()

    # Use effective (post-crop) parameters if available for display
    center_frequency = (getattr(run, 'freq_effective', run.freq)) / 1000
    span = (getattr(run, 'span_effective', run.span)) / 1000

    # Create figure early so we can query actual pixel width for decimation decision
    fig = plt.figure(figsize=(20, 8))

    fig_width_px = 1600  # Fallback if figure metrics unavailable (20in * 80 dpi)
    try:
        fig_width_px = int(fig.get_figwidth() * fig.get_dpi())
    except Exception:
        logging.warning("Could not determine figure metrics")
        pass

    waterfall_array = decimate_for_plot(waterfall_array, fig_width_px)

    start_freq = center_frequency - span / 2
    stop_freq = center_frequency + span / 2
    nbin = run.fft_size

    ax = plt.gca()
    ax.set_facecolor('black')

    set_x_axis(center_frequency, span, waterfall_array, ax)

    recording_duration_ms = run.rec_time_ms if hasattr(run, 'rec_time_ms') else 5000
    recording_duration_s = recording_duration_ms / 1000.0
    set_y_axis(recording_duration_s)

    # Create 1D coordinate vectors for efficient pcolormesh rendering
    num_rows = waterfall_array.shape[0]
    num_cols = waterfall_array.shape[1] - 1  # Subtract 1 because we slice [:, 1:]

    # Log data dimensions for performance analysis
    total_data_points = num_rows * num_cols
    logging.info(
        f"Data dimensions: {num_rows} rows × {num_cols} cols = {total_data_points:,} data points | FFT size: {nbin}")

    # Y coordinates: map from 0 to recording_duration_s
    y_coords = np.linspace(0, recording_duration_s, num_rows)
    # X coordinates: map frequency bins
    x_coords = np.arange(num_cols)

    # Use 1D coordinate vectors directly (no meshgrid needed - saves 66% memory)
    cmap = plt.cm.jet
    #    cmap = plt.cm.plasma # for spectral data

    mesh = plt.pcolormesh(x_coords, y_coords, waterfall_array[:, 1:],
                          cmap=cmap,
                          vmin=min_db_val,
                          vmax=max_db_val,
                          # norm=Normalize,
                          antialiased=False
                          )

    ax = mesh.axes
    ax.invert_yaxis()

    # Use actual data dimensions for pixel ratio
    pixel_ratio = num_cols / span
    # Draw MHz separators and band markers using axis height (upper/lower thirds)
    draw_lines(start_freq, stop_freq, pixel_ratio, ax)

    set_plot_title(run)


    # mesh.draw()
    # plot(peaks, x[peaks], "x")
    # plt.colorbar()

    # logging.info("write file " + filename)

    from timeit import default_timer as timer
    start = timer()
    plt.savefig(filename,
                bbox_inches="tight",
                pad_inches=0.2,
                transparent=False,
                facecolor="grey",
                edgecolor='w',
                pil_kwargs={'compress_level': png_compression_level}
                )
    plt.close('all')
    gc.collect()
    end = timer()
    savefig_time = end - start
    total_time = end - total_start

    # Track performance statistics
    track_performance("Plot generation", total_time)

    # Return save time so caller can aggregate with thumbnail time
    return savefig_time


def set_plot_title(run):

    # Use effective (post-crop) parameters if available for display
    center_frequency = (getattr(run, 'freq_effective', run.freq)) / 1000
    span = (getattr(run, 'span_effective', run.span)) / 1000

    font_size = 20

    # Titles: left shows date/time, center shows capture id, right shows span (kHz) and gain

    time_string = run.capture_start_time.strftime('[%H:%M:%S]')
    date_string = run.capture_start_time.strftime('%Y-%m-%d')

    left_text = f"{date_string} {time_string}"
    span_khz_value = int(round(span))
    right_text = f"span={span_khz_value} kHz  gain={get_config_manager().get('rf_gain')}"
    center_text = str(run.id)
    plt.title(left_text, fontsize=font_size, loc='left')
    plt.title(center_text , fontsize=font_size, loc='center')
    plt.title(right_text, fontsize=15, loc='right')


def decimate_for_plot(waterfall_array, fig_width_px):
    # Decimate based on rendered pixel width to preserve detail (~1 column per pixel)
    raw_cols = waterfall_array.shape[1]

    target_cols = max(1, fig_width_px)

    if raw_cols <= target_cols or raw_cols < 200:
        factor = 1
    else:
        factor_est = int(np.ceil(raw_cols / target_cols))
        allowed = [1, 2, 3, 4, 6, 8, 12, 16]
        factor = next((f for f in allowed if f >= factor_est), allowed[-1])

    if factor > 1:
        logging.info(f"Applying decimation (factor={factor}, method={decimation_method}) based on {raw_cols} cols and figure width {fig_width_px}px (target ~{target_cols} cols)")
    else:
        logging.info(f"Skipping decimation for {raw_cols} cols and figure width {fig_width_px}px (target ~{target_cols} cols)")

    return decimate_data(waterfall_array, factor, decimation_method)


def set_x_axis(center_frequency, span, waterfall_array, ax):

    start_freq = center_frequency - span / 2
    stop_freq = center_frequency + span / 2

    # Choose tick spacing to target a readable tick count (~20)
    desired_ticks = 20
    raw_interval = max(span / desired_ticks, 1)
    nice_steps = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000]
    tick_interval_khz = min(nice_steps, key=lambda s: abs(s - raw_interval))

    # Find the first tick position (round start_freq up to nearest tick interval)
    first_tick_freq = np.ceil(start_freq / tick_interval_khz) * tick_interval_khz

    # Generate frequency labels at the specified tick interval within the span
    xlabels = []
    freq = first_tick_freq
    while freq <= stop_freq + 1e-9:
        # Labels in integer kHz (no fractional ticks)
        xlabels.append(f"{int(round(freq))}")
        freq += tick_interval_khz

    # Compute current number of columns for tick mapping (post-decimation)
    num_cols_for_ticks = waterfall_array.shape[1] - 1  # we will slice [:, 1:] later

    # Convert frequency labels to corresponding FFT bin positions (use actual data size)
    xticks = []
    freq = first_tick_freq
    for freq_label in xlabels:
        # Map frequency to bin position: use actual decimated data size, not original nbin
        bin_position = (freq - start_freq) / span * num_cols_for_ticks
        xticks.append(bin_position)
        freq += tick_interval_khz

    # Debug logging for tick generation
    # logging.info(f"X-axis tick generation: span={span:.0f} kHz, tick_interval={tick_interval_khz} kHz")
    # logging.info(f"Generated {len(xlabels)} tick labels: {xlabels}")
    # logging.info(f"Tick positions in data coordinates: {xticks}")

    # Set ticks explicitly and disable automatic tick generation
    plt.xticks(xticks, xlabels)
    ax.xaxis.set_major_locator(FixedLocator(xticks))

def set_y_axis(recording_duration_s):

    # Create y-axis ticks at 1-second intervals based on actual time
    max_seconds = int(recording_duration_s) + 1
    ytick_seconds = np.arange(0, max_seconds, 1)

    # Filter ticks to only show those within recording duration
    valid_mask = ytick_seconds <= recording_duration_s
    ytick_seconds = ytick_seconds[valid_mask]

    plt.yticks(ytick_seconds, [f'{int(s)} s' for s in ytick_seconds])


def draw_lines(start_freq, stop_freq, pixel_ratio, ax):

    # Always use the current axis y-limits (image height) to place lines
    y0, y1 = ax.get_ylim()
    y_min = min(y0, y1)
    y_max = max(y0, y1)
    y_top_segment = [y_min + (y_max - y_min) * 2.0 / 3.0, y_max]     # Upper third
    y_bottom_segment = [y_min, y_min + (y_max - y_min) * 1.0 / 3.0]  # Lower third

    def draw_bandplan_line(f):
        if (f > start_freq) and (f < stop_freq):
            x2 = (f - start_freq) * pixel_ratio
            l1 = [x2 - 2, x2 - 2]
            l1_ = [x2 + 2, x2 + 2]
            ax.plot(l1, y_bottom_segment, '-.', linewidth=3, color='black')
            ax.plot(l1_, y_bottom_segment, '-.', linewidth=3, color='red')

    def draw_line(f):
        if (f > start_freq) and (f < stop_freq):
            x2 = (f - start_freq) * pixel_ratio
            l1 = [x2 - 2, x2 - 2]
            l1_ = [x2 + 2, x2 + 2]
            ax.plot(l1, y_top_segment, '-.', linewidth=3, color='black')
            ax.plot(l1_, y_top_segment, '-.', linewidth=3, color='white')

    if draw_mhz_separators:
        # Draw only MHz lines inside the current window for performance
        first_mhz = int(np.ceil(start_freq / 1000.0)) * 1000
        last_mhz = int(np.floor(stop_freq / 1000.0)) * 1000
        for x in range(int(first_mhz), int(last_mhz) + 1, 1000):
            draw_line(x)

    if draw_bandplan:
        for band in band_markers:
            draw_bandplan_line(band.start)
            draw_bandplan_line(band.end)
