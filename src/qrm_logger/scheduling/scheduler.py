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

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from qrm_logger.core.config_manager import get_config_manager
from qrm_logger.execution import get_pipeline


class Scheduler:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Scheduler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Scheduler._initialized:
            return
        self.running = False
        self._scheduler: BackgroundScheduler | None = None
        Scheduler._initialized = True


    def start_scheduler(self, cron: str | None = None):

        if self.running:
            logging.warning("Scheduler is already running")
            return False

        # Get cron expression from parameter or config
        if cron is None:
            cron = get_config_manager().get("scheduler_cron", None)

        if not cron:
            logging.error("No cron expression provided for scheduler")
            return False

        # Create a fresh APScheduler instance each start
        self._scheduler = BackgroundScheduler(job_defaults={
            "max_instances": 1,  # do not overlap runs
            "coalesce": True,    # collapse missed runs into one
            "misfire_grace_time": 1,  # avoid immediate catch-up runs
        })

        # Build cron trigger
        trigger = None
        try:
            trigger = CronTrigger.from_crontab(cron)
            logging.info(f"Starting scheduler with cron expression: '{cron}'")
        except Exception as e:
            logging.error(f"Invalid cron expression '{cron}': {e}")
            self._scheduler = None
            return False

        # Use a wrapper to construct fresh params per run
        def _run_capture_wrapper():
            # Delegate to Pipeline singleton
            get_pipeline().execute_capture_default()

        self._scheduler.add_job(
            _run_capture_wrapper,
            trigger=trigger,
            id="periodic_capture",
            replace_existing=True,
        )

        self._scheduler.start()
        self.running = True
        return True

    def stop_scheduler(self):
        logging.info("Stopping scheduler")
        self.running = False

        # Stop APScheduler and clear jobs
        if self._scheduler is not None:
            try:
                self._scheduler.remove_all_jobs()
            except Exception:
                pass
            try:
                self._scheduler.shutdown(wait=False)
            except Exception:
                pass
            self._scheduler = None

        return True

    def is_running(self):
        return self.running



    def get_next_scheduled_time(self):
        """Get the next scheduled execution time from APScheduler"""
        try:
            if not self._scheduler:
                return None
            jobs = self._scheduler.get_jobs()
            if not jobs:
                return None

            # Choose the job with the nearest next run time
            jobs = [j for j in jobs if getattr(j, 'next_run_time', None) is not None]
            if not jobs:
                return None
            next_run = min(jobs, key=lambda j: j.next_run_time).next_run_time
            if next_run:
                # Convert to local time and format as ISO 8601 with timezone for UI
                local_dt = next_run.astimezone()
                return local_dt.isoformat()
            return None
        except Exception as e:
            logging.error(f"Error getting next scheduled time: {e}")
            return None

    def get_status(self):
        job_count = 0
        try:
            if self._scheduler:
                job_count = len(self._scheduler.get_jobs())
        except Exception:
            job_count = 0
        return {
            'running': self.running,
            'scheduled_jobs_count': job_count
        }



# Singleton accessor

def get_scheduler() -> Scheduler:
    return Scheduler()


