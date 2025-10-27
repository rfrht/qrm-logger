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

from qrm_logger.core.config_manager import get_config_manager


def fmt_secs(secs: float) -> str:
    secs_int = int(round(secs))
    if secs_int < 60:
        return f"{secs_int} s"
    m, s = divmod(secs_int, 60)
    return f"{m} min {s} s"


def log_batch_summary(
    cancelled: bool,
    total_secs: float,
    record_secs: float,
    process_secs: float,
    sets_recorded,
):
    runs_info = ""
    try:
        # Determine planned run count
        num_runs_planned = 0
        if sets_recorded:
            try:
                num_runs_planned = sum(len(r) for (_, r) in sets_recorded)
            except Exception:
                num_runs_planned = 0

        rec_time_sec_value = float(get_config_manager().get("rec_time_default_sec") or 0)

        if rec_time_sec_value is not None and num_runs_planned > 0:
            completed_secs = num_runs_planned * float(rec_time_sec_value)
            rt_int = int(round(float(rec_time_sec_value)))
            runs_info = f" | runs={num_runs_planned} x {rt_int} s ≈ {fmt_secs(completed_secs)}"
    except Exception:
        pass

    # Build recording string with optional startup
    rec_str = fmt_secs(record_secs)

    if cancelled:
        logging.info(
            f"run cancelled after {fmt_secs(total_secs)} "
            f"(recording={rec_str}, processing={fmt_secs(process_secs)}){runs_info}"
        )
    else:
        logging.info(
            f"all runs processed in {fmt_secs(total_secs)} "
            f"(recording={rec_str}, processing={fmt_secs(process_secs)}){runs_info}"
        )


def log_raw_write_perf(
    total_ms: float,
    compressed_mb: float,
    uncompressed_mb: float,
    ratio_pct: float,
    compress_ms: float,
    shape,
):
    logging.info(
        f"PERF: Raw write: total={total_ms:.1f} ms | "
        f"saved={compressed_mb:.2f} MB ({ratio_pct:.1f}%) | "
        f"uncompressed={uncompressed_mb:.2f} MB, compression={compress_ms:.1f} ms | "
        f"shape={shape}"
    )


def log_time_to_first_fft_frame(elapsed_ms: float):
    logging.info(f"PERF: Time to first FFT frame after start: {elapsed_ms:.1f} ms")



def log_perf_sdr_source_creation(elapsed_ms: float):
    logging.info(f"PERF: SDR source creation took {elapsed_ms:.1f} ms")

