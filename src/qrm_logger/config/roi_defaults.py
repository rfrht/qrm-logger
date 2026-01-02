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
This template is used to generate config-roi.json on first start.
"""

DEFAULT_ROI_JSON = """{
  "processing_enabled": true,
  "rois": [
    {
      "roi_id": "FT8 160m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "160m",
      "center_khz": 1842,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 80m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "80m",
      "center_khz": 3574,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 60m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "60m",
      "center_khz": 5358,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 40m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "40m",
      "center_khz": 7075,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 30m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "30m",
      "center_khz": 10137,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 20m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "20m",
      "center_khz": 14075,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 17m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "17m",
      "center_khz": 18101,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 15m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "15m",
      "center_khz": 21076,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 12m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "12m",
      "center_khz": 24916,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 10m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "10m",
      "center_khz": 28076,
      "span_khz": 5
    },
    {
      "roi_id": "FT8 6m",
      "base_capture_set_id": "HF_bands",
      "capture_spec_id": "6m",
      "center_khz": 50316,
      "span_khz": 5
    }
  ]
}"""
