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
Scheduler configuration settings for QRM Logger.
Contains automated recording schedule parameters and timing settings.
"""

from .toml_config import _toml

# =============================================================================
# SCHEDULER CONFIGURATION
# =============================================================================

# Automatically start the scheduler when the application starts from command line
# If True: scheduler starts immediately when main.py runs
# If False: scheduler must be started manually via web interface
# dynamic property, managed by config-dynamic.json
scheduler_autostart = _toml["scheduler"]["autostart"]

# Cron expression in standard crontab format
# Tip: Prefer day-of-week names (mon-sun) instead of numbers to avoid ambiguity with APScheduler's DOW mapping (0=Mon..6=Sun).
# Examples:
#   "*/15 * * * *"              -> every 15 minutes
#   "0 * * * *"                 -> at minute 0 of every hour
#   "*/5 18-21 * * *"           -> every 5 minutes from 18:00 to 21:59
#   "*/10 6-8,17-20 * * mon-fri" -> every 10 minutes during commute hours on weekdays
# dynamic property, managed by config-dynamic.json
scheduler_cron = _toml["scheduler"]["cron"]
