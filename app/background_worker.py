import logging
import time
import threading
import os
import sys
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone, utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app import create_app, db
from app.models import User, Settings
from .feed_updater import update_feeds_thread
from .feed_cleaner import clean_feeds

app = create_app()
lock = threading.Lock()
LOCKFILE = "/tmp/scheduler.lock"
save_update_interval = None
running = True


def is_another_instance_running():
    """
    Checks if another instance of the scheduler is running.

    Returns:
        bool: True if another instance is running, False otherwise.
    """
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
    """
    Removes the lockfile if it exists.

    This function attempts to remove the lockfile specified by the `LOCKFILE`
    constant. If the lockfile exists, it is deleted and a debug message is
    logged.

    """
    logging.debug("Attempting to remove lockfile")
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        logging.debug("Lockfile removed")


def schedule_jobs(scheduler, app):
    """
    Schedules jobs for the background worker based on user settings.
    Args:
        scheduler (apscheduler.Scheduler): The scheduler to add jobs to.
        app (Flask): The Flask application object.
    Returns:
        None
    """
    # Acquire lock to prevent concurrent updates to database
    with lock:
        # Set the app context for the current thread
        with app.app_context():
            # Query the first user in the database
            user = db.session.query(User).first()

            if user:  # If there is a user present
                # Get the timezone from the user settings and convert it to pytz format
                user_timezone = pytz_timezone(user.settings.timezone)

                # Convert user's last sync time to the user's timezone
                last_sync = user.last_sync
                if last_sync is None:
                    last_sync = datetime.min.replace(tzinfo=utc).astimezone(user_timezone)
                else:
                    if last_sync.tzinfo is None:
                        last_sync = utc.localize(last_sync).astimezone(user_timezone)
                    else:
                        last_sync = last_sync.astimezone(user_timezone)

                # Get the update interval from the user settings in minutes
                update_interval_minutes = user.settings.update_interval

                # Calculate when the next run time should be based on the update interval and last sync time
                next_run_time = last_sync + timedelta(minutes=update_interval_minutes)
                now = datetime.now(user_timezone)

                if next_run_time <= now:  # If the next run time is before or equal to the current time
                    next_run_time = now  # Set the next run time to now to ensure immediate execution
                    scheduler.add_job(
                        update_feeds_thread,
                        DateTrigger(run_date=next_run_time),
                        id="update_feeds_job_immediate",
                        replace_existing=True,
                        args=[app],
                    )
                    logging.info(
                        "Update feeds job scheduled to run immediately"
                    )

                scheduler.add_job(
                    update_feeds_thread,
                    IntervalTrigger(minutes=update_interval_minutes, timezone=user_timezone),
                    id="update_feeds_job",
                    replace_existing=True,
                    args=[app],
                )
                logging.info(
                    "Update feeds job scheduled to run every %d minutes",
                    update_interval_minutes,
                )

                # Schedule the clean feeds job to run immediately and then every 3 hours
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
                        "Clean feeds job scheduled to run immediately and then every 3 hours"
                    )


def run_scheduler():
    """
    Run the scheduler to update and clean feeds.

    This function is responsible for initiating and running the main scheduling
    process for updating and cleaning feeds in a Flask application. It first
    checks if there is an existing lockfile, and if not, it creates one with
    the current process ID (PID). Then, it retrieves user information from the
    database, calculates the next update time based on the user's settings,
    schedules the `update_feeds_thread` job to run immediately, and then at a
    specified interval. Additionally, it schedules the `clean_feeds` job to run
    immediately and then every three hours. Finally, it logs relevant
    information about the scheduling process.

    """
    global running
    remove_lockfile()
    if is_another_instance_running():
        logging.debug(
            "Another instance of the scheduler is already running. Exiting."
        )
        sys.exit(1)

    scheduler = BackgroundScheduler()
    schedule_jobs(scheduler, app)
    scheduler.start()
    logging.info("Scheduler started")

    try:
        while running:
            with app.app_context():
                last_sync = db.session.query(User).first().last_sync
                settings = db.session.query(Settings).first()
                update_interval = settings.update_interval

            global save_update_interval
            if update_interval != save_update_interval or last_sync is None:
                save_update_interval = (
                    update_interval if last_sync is not None else 0
                )
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
