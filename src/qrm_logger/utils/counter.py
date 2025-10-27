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
File-based counter for tracking recording sequence numbers.
Provides persistent counter functionality across application restarts.
"""
import logging
import os
from qrm_logger.config.output_directories import output_directory

counter_fname = os.path.join(output_directory, "counter.txt")

counter_value=-1

def get_counter():
    global counter_value

    if counter_value != -1:
        return counter_value
    else:
        if not os.path.exists(counter_fname):
            os.makedirs(output_directory, exist_ok=True)
            with open(counter_fname, "w") as file:
                file.write("0")
                file.close()

        with open(counter_fname, "r") as file:
            fdata = file.read()
            logging.info("read counter '"+str(fdata)+"'")
            counter_value = int(fdata)
            file.close()
            return counter_value


def inc_counter():
    global counter_value
    get_counter()
    counter_value += 1

    with open(counter_fname, "w") as file:
        file.write(str(counter_value))
        file.close()
    return counter_value
