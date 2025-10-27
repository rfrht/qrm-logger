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
Web server configuration settings for QRM Logger.
Contains network binding and server parameter settings for the web interface.
"""

# =============================================================================
# WEB SERVER CONFIGURATION
# =============================================================================

# Web server host and port settings
# Default: 'localhost' - Only accessible from local machine
# For network access: Use '0.0.0.0' to bind to all interfaces
# WARNING: Using '0.0.0.0' makes the server accessible to anyone on your network.
#          Only use this on trusted networks as there is no authentication.
# Examples:
#   web_server_host = 'localhost'     # Local access only (secure)
#   web_server_host = '0.0.0.0'       # Network access (SECURITY RISK on untrusted networks)
#   web_server_host = '192.168.1.100' # Specific IP address
web_server_host = 'localhost'
#web_server_host = '0.0.0.0'
web_server_port = 7060

# Static file cache control (seconds)
# Sets Cache-Control: public, max-age=<value> for Bottle static_file responses.
# Set to 0 to disable caching (no-store).
#static_cache_max_age_sec = 3600
static_cache_max_age_sec = 0

