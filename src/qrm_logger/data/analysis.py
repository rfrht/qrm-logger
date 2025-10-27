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
RMS analysis functionality for spectrum data processing.
Provides quantitative measurements for QRM detection and interference analysis.
"""

import logging
import numpy as np

from qrm_logger.config.analysis import exclude_freqs_khz
from qrm_logger.data.log import collect_log_text


def build_include_mask(n_bins, center_frequency, span, exclude_freqs_khz=None, half_window_khz=1.0, run=None):
    """
    Build a boolean inclusion mask that excludes specified frequency windows
    around given center frequencies.

    Semantics: True = include this bin, False = exclude this bin.

    Args:
        n_bins: Number of FFT bins (len of spectrum)
        center_frequency: Center frequency in kHz
        span: Frequency span in kHz
        exclude_freqs_khz: Iterable of center frequencies (kHz) to exclude
        half_window_khz: Half-width around each frequency to exclude (default 1.0 kHz)
        run: Optional run context used for log collection

    Returns:
        numpy.ndarray: Boolean mask with True for bins to include and False for excluded bins
    """
    start_freq = center_frequency - span / 2
    freq_per_bin = span / n_bins

    include_mask = np.ones(n_bins, dtype=bool)
    
    # Track if anything is actually excluded
    exclusions_made = False

    for f0 in (exclude_freqs_khz or []):
        exc_start = f0 - half_window_khz
        exc_end = f0 + half_window_khz

        start_bin = int(round((exc_start - start_freq) / freq_per_bin))
        end_bin = int(round((exc_end - start_freq) / freq_per_bin))

        start_bin = max(0, start_bin)
        end_bin = min(n_bins - 1, end_bin)

        if start_bin <= end_bin and start_bin < n_bins and end_bin >= 0:
            actual_start_freq = start_freq + (start_bin * freq_per_bin)
            actual_end_freq = start_freq + (end_bin * freq_per_bin)

            if run is not None:
                collect_log_text(run, 'build_include_mask', f"Excluding around {f0:.1f} kHz:")
                collect_log_text(run, 'build_include_mask', f"  Target exclusion: {exc_start:.1f} to {exc_end:.1f} kHz")
                collect_log_text(run, 'build_include_mask', f"  Actual exclusion: {actual_start_freq:.1f} to {actual_end_freq:.1f} kHz")
                collect_log_text(run, 'build_include_mask', f"  Excluded bins: {start_bin} to {end_bin} ({end_bin - start_bin + 1} bins)")

            include_mask[start_bin:end_bin + 1] = False
            exclusions_made = True

    if exclusions_made and run is not None:
        collect_log_text(run, 'build_include_mask', "Building inclusion mask")
        collect_log_text(run, 'build_include_mask', f"  Frequency span: {start_freq:.1f} to {start_freq + span:.1f} kHz")
        collect_log_text(run, 'build_include_mask', f"  Bin bandwidth = {freq_per_bin:.3f} kHz")
        collect_log_text(run, 'build_include_mask', f"  Half-window: ±{half_window_khz:.1f} kHz")
        if exclude_freqs_khz:
            collect_log_text(run, 'build_include_mask', f"  Targets: {', '.join(f'{f:.1f} kHz' for f in exclude_freqs_khz)}")
    
    return include_mask


def find_strong_peaks(avg_wf_filtered, original_indices, start_freq, freq_per_bin, median_linear_power, 
                      max_peaks=5, min_separation_khz=3.0, min_ratio=100):
    """
    Find strong peaks in the spectrum with minimum frequency separation.
    
    Args:
        avg_wf_filtered: Filtered spectrum data in dB
        original_indices: Original indices that weren't excluded
        start_freq: Start frequency in kHz
        freq_per_bin: Frequency per bin in kHz
        median_linear_power: Median linear power for ratio calculation
        max_peaks: Maximum number of peaks to return (default: 5)
        min_separation_khz: Minimum separation between peaks in kHz (default: 3.0)
        min_ratio: Minimum ratio compared to median to be considered strong (default: 100)
        
    Returns:
        List of peak dictionaries with 'freq', 'power_db', 'ratio', 'bin_idx' keys
    """
    # Convert filtered spectrum to linear power
    linear_power_filtered = 10**(avg_wf_filtered / 10)
    
    # Find peaks that are stronger than the minimum ratio
    strong_peak_mask = linear_power_filtered > (median_linear_power * min_ratio)
    strong_indices = np.where(strong_peak_mask)[0]
    
    if len(strong_indices) == 0:
        return []
    
    # Get power values and sort by strength (descending)
    strong_powers = linear_power_filtered[strong_indices]
    sorted_order = np.argsort(strong_powers)[::-1]  # Descending order
    
    peaks = []
    min_separation_bins = int(min_separation_khz / freq_per_bin)
    
    for idx in sorted_order:
        if len(peaks) >= max_peaks:
            break
            
        candidate_bin_filtered = strong_indices[idx]
        candidate_bin_original = original_indices[candidate_bin_filtered]
        candidate_freq = start_freq + (candidate_bin_original * freq_per_bin)
        
        # Check separation from existing peaks
        too_close = False
        for existing_peak in peaks:
            freq_diff = abs(candidate_freq - existing_peak['freq'])
            if freq_diff < min_separation_khz:
                too_close = True
                break
        
        if not too_close:
            power_linear = strong_powers[idx]
            power_db = avg_wf_filtered[candidate_bin_filtered]
            ratio = power_linear / median_linear_power
            
            peaks.append({
                'freq': candidate_freq,
                'power_db': power_db,
                'ratio': ratio,
                'bin_idx': candidate_bin_original
            })
    
    # Sort peaks by strength (strongest first) for output
    peaks.sort(key=lambda x: x['ratio'], reverse=True)
    
    return peaks


def build_core_rms_mask(n_bins, start_freq, freq_per_bin, run):
    """
    Build an inclusion mask for RMS that keeps only the core freq_range
    (excluding margins). If no freq_range is set, returns all-True.
    """
    fr = getattr(getattr(run, 'spec', None), 'freq_range', None)
    if fr is None:
        return np.ones(n_bins, dtype=bool)

    core_start_khz = fr.freq_start
    core_end_khz = fr.freq_end

    start_bin_core = int(np.ceil((core_start_khz - start_freq) / freq_per_bin))
    end_bin_core = int(np.floor((core_end_khz - start_freq) / freq_per_bin))

    start_bin_core = max(0, min(n_bins - 1, start_bin_core))
    end_bin_core = max(0, min(n_bins - 1, end_bin_core))

    mask = np.zeros(n_bins, dtype=bool)
    if end_bin_core >= start_bin_core:
        mask[start_bin_core:end_bin_core + 1] = True

    collect_log_text(run, 'calculate_rms', f"RMS window (core): {core_start_khz:.1f}-{core_end_khz:.1f} kHz -> bins {start_bin_core}-{end_bin_core}")
    return mask


def calculate_rms(run, data, min_db_val, max_db_val):
    """
    Calculate RMS with exclusion of specified frequency ranges.
    Default exclusion targets include SDR artifacts around 0 kHz and 28800 kHz.
    
    Args:
        run: CaptureRun object containing frequency and span information
        data: Pre-loaded FFT data array (numpy 2D array)
        min_db_val: Minimum dB value for normalization
        max_db_val: Maximum dB value for normalization
        collect_logs: Whether to collect detailed log messages for this run
        
    Returns:
        tuple: (rms_normalized, exclude_mask, rms_truncated_5)
    """
    # Calculate average spectrum over time
    avg_wf = np.mean(data, axis=0)
    
    # Convert effective run frequency/span from Hz to kHz for analysis (fallback to original)
    freq_hz = getattr(run, 'freq_effective', run.freq)
    span_hz = getattr(run, 'span_effective', run.span)
    center_frequency = freq_hz / 1000
    span = span_hz / 1000
    
    # Linear Domain RMS calculation
    # Convert dB to linear power scale for physically meaningful RMS
    linear_power = 10**(avg_wf / 10)  # dB to linear power conversion

    # Frequency axis basics
    start_freq = center_frequency - span / 2
    freq_per_bin = span / len(avg_wf)

    # Build exclusion mask for specified frequencies (configurable)
    include_mask_global = build_include_mask(len(avg_wf), center_frequency, span, exclude_freqs_khz, run=run)

    # Build RMS core mask (no margins) and combine with global exclusions
    core_mask = build_core_rms_mask(len(avg_wf), start_freq, freq_per_bin, run)
    include_mask = include_mask_global & core_mask
    included_count = int(np.count_nonzero(include_mask))
    total_bins = len(avg_wf)
    collect_log_text(run, 'calculate_rms', f"RMS bins kept: {included_count}/{total_bins}")
    if included_count == 0:
        collect_log_text(run, 'calculate_rms', 'WARNING: No bins left after applying exclusions + core window; returning empty RMS')
        return None, include_mask, None

    # Apply exclusion mask to both dB and linear power arrays for RMS calculation
    linear_power_filtered = linear_power[include_mask]
    avg_wf_filtered = avg_wf[include_mask]
    
    # Detailed logging for diagnosis - find extreme values (using filtered data)
    max_db_signal = np.max(avg_wf_filtered)
    min_db_signal = np.min(avg_wf_filtered)
    max_linear_power = np.max(linear_power_filtered)
    min_linear_power = np.min(linear_power_filtered)
    median_db_signal = np.median(avg_wf_filtered)
    median_linear_power = np.median(linear_power_filtered)
    
    # Find indices of extreme values using filtered data (excluding 0 kHz)
    max_idx_filtered = np.argmax(avg_wf_filtered)
    min_idx_filtered = np.argmin(avg_wf_filtered)
    
    # Map filtered indices back to original array indices
    # Create array of original indices that weren't excluded
    original_indices = np.arange(len(avg_wf))[include_mask]
    max_idx = original_indices[max_idx_filtered]
    min_idx = original_indices[min_idx_filtered]
    
    # Calculate frequencies for the extreme values
    # Map FFT bin to actual frequency
    max_freq = start_freq + (max_idx * freq_per_bin)
    min_freq = start_freq + (min_idx * freq_per_bin)
    
    # Calculate how much the strongest signal dominates
    power_ratio = max_linear_power / median_linear_power if median_linear_power > 0 else 0
    
    collect_log_text(run, 'calculate_rms', f"Signal Analysis:")
    collect_log_text(run, 'calculate_rms', f"  Strongest: {max_db_signal:.1f} dB at {max_freq:.0f} kHz (bin {max_idx})")
    collect_log_text(run, 'calculate_rms', f"  Weakest: {min_db_signal:.1f} dB at {min_freq:.0f} kHz (bin {min_idx})")
    collect_log_text(run, 'calculate_rms', f"  Median: {median_db_signal:.1f} dB")
    collect_log_text(run, 'calculate_rms', f"  Peak/Median ratio: {power_ratio:.1f}x")
    collect_log_text(run, 'calculate_rms', f"  Signal range: {max_db_signal - min_db_signal:.1f} dB")
    
    # Calculate RMS in linear domain using filtered data (excluding 0 kHz)
    rms_linear = np.sqrt(np.mean(linear_power_filtered**2))
    
    # Calculate what the RMS would be without the strongest signal (for comparison)
    # Use filtered data for this calculation too
    linear_power_no_peak = np.copy(linear_power_filtered)
    max_idx_filtered2 = np.argmax(linear_power_filtered)
    linear_power_no_peak[max_idx_filtered2] = median_linear_power  # Replace peak with median
    rms_linear_no_peak = np.sqrt(np.mean(linear_power_no_peak**2))
    
    # Convert RMS back to dB domain for easier normalization
    rms_db = 10 * np.log10(rms_linear) if rms_linear > 0 else -100
    rms_db_no_peak = 10 * np.log10(rms_linear_no_peak) if rms_linear_no_peak > 0 else -100
    
    # Normalize RMS in dB domain using config range (much more stable)
    # This avoids tiny linear numbers and provides better scaling
    if max_db_val > min_db_val:
        rms_normalized = ((rms_db - min_db_val) / (max_db_val - min_db_val)) * 100
    else:
        rms_normalized = 0
    
    # Clamp only negative values to prevent negative RMS
    # Allow values above 100 for better analysis of strong signals
    rms_normalized = max(0, rms_normalized)
    
    # Calculate truncated RMS for comparison (5% and 10%)
    truncated_rms_5, threshold_db_5, capped_bins_5 = calculate_truncated_rms(
        avg_wf, center_frequency, span, min_db_val, max_db_val, include_mask, 5
    )
    truncated_rms_10, threshold_db_10, capped_bins_10 = calculate_truncated_rms(
        avg_wf, center_frequency, span, min_db_val, max_db_val, include_mask, 10
    )
    
    collect_log_text(run, 'calculate_rms', f"RMS Analysis:")
    collect_log_text(run, 'calculate_rms', f"  Full RMS: Linear={rms_linear:.2e}, dB={rms_db:.1f}, Normalized={rms_normalized:.1f}%")
    collect_log_text(run, 'calculate_rms', f"  RMS without peak: dB={rms_db_no_peak:.1f} (diff: {rms_db - rms_db_no_peak:.1f} dB)")
    collect_log_text(run, 'calculate_rms', f"  Truncated RMS (5%): {truncated_rms_5:.1f}% (capped {capped_bins_5} bins at {threshold_db_5:.1f} dB)")
    collect_log_text(run, 'calculate_rms', f"  Truncated RMS (10%): {truncated_rms_10:.1f}% (capped {capped_bins_10} bins at {threshold_db_10:.1f} dB)")
    
    # Compare standard vs truncated (using 10% as primary comparison)
    rms_diff_10 = abs(rms_normalized - truncated_rms_10)
    rms_diff_5 = abs(rms_normalized - truncated_rms_5)
    if rms_diff_10 > 15:
        collect_log_text(run, 'calculate_rms', f"  -> Large RMS difference (10%: {rms_diff_10:.1f}pp, 5%: {rms_diff_5:.1f}pp) suggests narrowband interference")
    
    # Find multiple strong peaks with minimum separation
    if power_ratio > 100:
        # Find up to 5 strong peaks with at least 3 kHz separation
        strong_peaks = find_strong_peaks(avg_wf_filtered, original_indices, start_freq, freq_per_bin, 
                                       median_linear_power, max_peaks=5, min_separation_khz=3.0)
        
        if len(strong_peaks) == 1:
            peak = strong_peaks[0]
            collect_log_text(run, 'calculate_rms', f"Strong peak detected at {peak['freq']:.0f} kHz! Peak is {peak['ratio']:.0f}x stronger than median - may dominate RMS")
        else:
            collect_log_text(run, 'calculate_rms', f"Multiple strong peaks detected ({len(strong_peaks)} peaks):")
            for i, peak in enumerate(strong_peaks, 1):
                collect_log_text(run, 'calculate_rms', f"  Peak {i}: {peak['freq']:.0f} kHz ({peak['power_db']:.1f} dB) - {peak['ratio']:.0f}x stronger than median")

    return rms_normalized, include_mask, truncated_rms_5


def calculate_truncated_rms(avg_wf, center_frequency, span, min_db_val, max_db_val, include_mask=None, truncation_pct=10):
    """
    Calculate an alternative RMS that truncates the strongest signals to be more robust
    against narrowband interference.
    
    Args:
        avg_wf: Average waterfall spectrum data in dB
        center_frequency: Center frequency in kHz
        span: Frequency span in kHz
        min_db_val: Minimum dB value for normalization
        max_db_val: Maximum dB value for normalization
        include_mask: Optional inclusion mask to select bins for RMS (e.g., from calculate_rms)
        truncation_pct: Percentage of strongest signals to truncate (default 10%)
        
    Returns:
        tuple: (truncated_rms_normalized, threshold_db, capped_bins) 
    """
    
    # Apply inclusion mask if provided (e.g., to use only selected bins)
    if include_mask is not None:
        avg_wf_filtered = avg_wf[include_mask]
    else:
        avg_wf_filtered = avg_wf.copy()
    
    # Convert to linear domain for mathematically correct truncation
    linear_power_filtered = 10**(avg_wf_filtered / 10)
    
    # Calculate threshold for truncation in LINEAR domain (remove top X% of values)
    threshold_percentile = 100 - truncation_pct
    threshold_linear = np.percentile(linear_power_filtered, threshold_percentile)
    
    # Cap values above threshold in LINEAR domain
    truncated_linear = linear_power_filtered.copy()
    capped_bins = np.sum(truncated_linear > threshold_linear)
    truncated_linear[truncated_linear > threshold_linear] = threshold_linear
    
    # Convert threshold back to dB for logging
    threshold_db = 10 * np.log10(threshold_linear) if threshold_linear > 0 else -100
    trunc_rms_linear = np.sqrt(np.mean(truncated_linear**2))
    trunc_rms_db = 10 * np.log10(trunc_rms_linear) if trunc_rms_linear > 0 else -100
    
    # Normalize
    if max_db_val > min_db_val:
        trunc_rms_normalized = ((trunc_rms_db - min_db_val) / (max_db_val - min_db_val)) * 100
    else:
        trunc_rms_normalized = 0
    
    trunc_rms_normalized = max(0, trunc_rms_normalized)
    
    return trunc_rms_normalized, threshold_db, capped_bins


