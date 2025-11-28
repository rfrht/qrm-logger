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
Default ROI (Regions of Interest) configuration for QRM Logger.
This template is used to generate roi-config.json on first start.
"""

DEFAULT_ROI_JSON = """{
  "processing_enabled": true,
  "rois": [
    {
      "roi_id": "FT8 80m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "80m",
      "center_khz": 3573,
      "span_khz": 10
    },
    {
      "roi_id": "FT8 40m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "40m",
      "center_khz": 7074,
      "span_khz": 10
    },
    {
      "roi_id": "FT8 20m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "20m",
      "center_khz": 14074,
      "span_khz": 10
    },
    {
      "roi_id": "FT8 15m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "15m",
      "center_khz": 21074,
      "span_khz": 10
    },
    {
      "roi_id": "FT8 10m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "10m",
      "center_khz": 28074,
      "span_khz": 10
    }
  ]
}"""
