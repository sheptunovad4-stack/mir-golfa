"""Daily schedule: run source monitor at 06:00 Europe/Moscow."""
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from app.collectors.monitor import run_all

def main():
    hour = int(os.getenv("GOLF_CIS_RUN_HOUR", "6"))
    minute = int(os.getenv("GOLF_CIS_RUN_MINUTE", "0"))
    scheduler = BlockingScheduler(timezone="Europe/Moscow")
    scheduler.add_job(run_all, CronTrigger(hour=hour, minute=minute),
                      id="daily_source_monitor", replace_existing=True,
                      max_instances=1, coalesce=True)
    print(f"Golf CIS source monitor scheduled daily at {hour:02d}:{minute:02d} Europe/Moscow")
    scheduler.start()

if __name__ == "__main__":
    main()
