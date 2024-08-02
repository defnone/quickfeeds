import logging
import time
import threading
import os
import sys
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone, utc
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app import create_app, db
from app.models import User, Settings
from .feed_updater import update_feeds_thread
from .feed_cleaner import clean_feeds
from .daily_updater import process_and_summarize_articles

app = create_app()
lock = threading.Lock()
LOCKFILE = "/tmp/scheduler.lock"
save_update_interval = None
save_daily_sync = None
running = True


def is_another_instance_running():
    logging.debug("Checking for another instance of the scheduler")
    if os.path.exists(LOCKFILE):
        with open(LOCKFILE, "r", encoding="UTF-8") as f:
            pid = f.read().strip()
            if pid and pid.isdigit():
                try:
                    os.kill(int(pid), 0)
                except OSError:
                    logging.debug("No process found with PID from lockfile")
                else:
                    logging.debug(
                        "Process with PID %s is already running", pid
                    )
                    return True

    with open(LOCKFILE, "w", encoding="UTF-8") as f:
        f.write(str(os.getpid()))
    logging.debug("Lockfile created with PID %s", os.getpid())
    return False


def remove_lockfile():
    "Remove the lock file function on startup and exit."
    logging.debug("Attempting to remove lockfile")
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        logging.debug("Lockfile removed")


def process_and_summarize_articles_with_context(app):
    with app.app_context():
        start_time = datetime.now(utc)
        process_and_summarize_articles()
        end_time = datetime.now(utc)

        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = duration_seconds / 60

        user = db.session.query(User).first()
        user.settings.daily_last_sync_time_duration = int(duration_minutes)

        user.daily_sync_at += relativedelta(days=1)

        db.session.commit()

        logging.info("Task completed in %s minutes", duration_minutes)


def schedule_daily_sync(scheduler, app):
    with app.app_context():
        user = db.session.query(User).first()

        if user and user.settings.daily_active:
            daily_sync_at = user.daily_sync_at
            daily_last_sync_time_duration = (
                user.settings.daily_last_sync_time_duration
            )

            if daily_sync_at is None:
                logging.info("daily_sync_at is None, skipping scheduling")
                return

            logging.info("daily_sync_at: %s", daily_sync_at)

            daily_sync_at = daily_sync_at.replace(tzinfo=utc)

            if daily_last_sync_time_duration is None:
                daily_last_sync_time_duration = timedelta(minutes=30)
            else:
                daily_last_sync_time_duration = timedelta(
                    minutes=daily_last_sync_time_duration
                )

            run_time = (
                daily_sync_at
                - daily_last_sync_time_duration
                - timedelta(minutes=10)
            )
            now = datetime.now(utc)

            logging.info(
                "Calculated run_time: %s, current time: %s", run_time, now
            )

            if run_time <= now:
                run_time = now + timedelta(minutes=3)
                logging.info(
                    "run_time is in the past, "
                    "setting run_time to 3 minutes from now"
                )

            scheduler.add_job(
                process_and_summarize_articles_with_context,
                DateTrigger(run_date=run_time),
                id="daily_sync_job",
                replace_existing=True,
                args=[app],
            )
            logging.info("Daily sync job scheduled to run at %s", run_time)


def schedule_update_feeds_job(scheduler, app, user, first_run):
    user_timezone = pytz_timezone(user.settings.timezone)
    last_sync = user.last_sync
    if last_sync is None:
        last_sync = datetime.min.replace(tzinfo=utc).astimezone(user_timezone)
    else:
        if last_sync.tzinfo is None:
            last_sync = utc.localize(last_sync).astimezone(user_timezone)
        else:
            last_sync = last_sync.astimezone(user_timezone)

    update_interval_minutes = user.settings.update_interval
    next_run_time = last_sync + timedelta(minutes=update_interval_minutes)
    now = datetime.now(user_timezone)

    if next_run_time <= now or first_run:
        next_run_time = now
        first_run = False
        scheduler.add_job(
            update_feeds_thread,
            DateTrigger(run_date=next_run_time),
            id="update_feeds_job_immediate",
            replace_existing=True,
            args=[app],
        )
        logging.info("Update feeds job scheduled to run immediately")

    scheduler.add_job(
        update_feeds_thread,
        IntervalTrigger(
            minutes=update_interval_minutes, timezone=user_timezone
        ),
        id="update_feeds_job",
        replace_existing=True,
        args=[app],
    )
    logging.info(
        "Update feeds job scheduled to run every %d minutes",
        update_interval_minutes,
    )


def schedule_clean_feeds_job(scheduler, app, user):
    user_timezone = pytz_timezone(user.settings.timezone)
    now = datetime.now(user_timezone)

    job_id = "clean_feeds"
    if not scheduler.get_job(job_id):
        scheduler.add_job(
            clean_feeds,
            DateTrigger(run_date=now),
            id=f"{job_id}_immediate",
            replace_existing=True,
            args=[app],
        )
        scheduler.add_job(
            clean_feeds,
            IntervalTrigger(hours=3, timezone=user_timezone),
            id=job_id,
            replace_existing=True,
            args=[app],
        )
        logging.info(
            "Clean feeds job scheduled to"
            "run immediately and then every 3 hours"
        )


def schedule_jobs(scheduler, app, first_run=False):
    with lock:
        with app.app_context():
            user = db.session.query(User).first()

            if user:
                schedule_update_feeds_job(scheduler, app, user, first_run)
                schedule_clean_feeds_job(scheduler, app, user)
                schedule_daily_sync(scheduler, app)


def run_scheduler():
    global running
    remove_lockfile()
    if is_another_instance_running():
        logging.debug(
            "Another instance of the scheduler is already running. Exiting."
        )
        sys.exit(1)

    scheduler = BackgroundScheduler()
    schedule_jobs(scheduler, app, first_run=True)
    scheduler.start()
    logging.info("Scheduler started")

    try:
        while running:
            with app.app_context():
                last_sync = db.session.query(User).first().last_sync
                settings = db.session.query(Settings).first()
                user = db.session.query(User).first()
                update_interval = settings.update_interval
                daily_sync = user.daily_sync_at

            global save_update_interval
            if update_interval != save_update_interval or last_sync is None:
                save_update_interval = (
                    update_interval if last_sync is not None else 0
                )
                schedule_jobs(scheduler, app)

            global save_daily_sync
            if daily_sync != save_daily_sync:
                save_daily_sync = daily_sync
                schedule_jobs(scheduler, app)

            time.sleep(30)

    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler shut down")
        scheduler.shutdown()
        remove_lockfile()
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        remove_lockfile()
    finally:
        logging.info("Exiting scheduler loop")
        running = False


if __name__ == "__main__":
    try:
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.start()
        logging.info("Background worker started in a separate thread")

        scheduler_thread.join()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down background worker")
        remove_lockfile()
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        remove_lockfile()
