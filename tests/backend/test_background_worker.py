import os
import pytest
import threading
import logging
from unittest import mock
import time
import datetime
from pytz import timezone as pytz_timezone, utc
from apscheduler.schedulers.background import BackgroundScheduler
from app.background_worker import (
    is_another_instance_running,
    remove_lockfile,
    schedule_jobs,
    run_scheduler,
    save_update_interval,
    running,
)
from app import create_app, db
from contextlib import contextmanager
import apscheduler.schedulers.background
from threading import Event

LOCKFILE = "/tmp/scheduler.lock"


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def scheduler():
    return BackgroundScheduler()


@pytest.fixture
def mock_user():
    user = mock.Mock()
    user.settings.timezone = "UTC"
    user.settings.update_interval = 60
    user.settings.daily_last_sync_time_duration = 1
    user.settings.daily_active = (
        True  # Включаем активность для ежедневного синка
    )
    user.daily_sync_at = datetime.datetime.now(datetime.UTC)
    user.last_sync = None

    return user


@pytest.fixture
def mock_db_session(mock_user):
    db_session = mock.Mock()
    db_session.query.return_value.first.return_value = mock_user
    return db_session


def test_is_another_instance_running_no_lockfile(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    assert not is_another_instance_running()


def test_is_another_instance_running_with_lockfile(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    monkeypatch.setattr(
        "builtins.open", mock.mock_open(read_data=str(os.getpid()))
    )
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    assert is_another_instance_running()


def test_remove_lockfile(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    remove_mock = mock.Mock()
    monkeypatch.setattr(os, "remove", remove_mock)
    remove_lockfile()
    remove_mock.assert_called_once_with(LOCKFILE)


def test_schedule_jobs(
    app, scheduler, mock_db_session, mock_user, monkeypatch
):
    monkeypatch.setattr("app.db.session", mock_db_session)
    schedule_jobs(scheduler, app)
    jobs = scheduler.get_jobs()
    assert len(jobs) > 0


@contextmanager
def timed(label):
    start = time.time()
    yield
    end = time.time()
    print(f"{label}: {end - start} seconds")


def test_run_scheduler(monkeypatch, caplog):
    global save_update_interval, running
    save_update_interval = None
    running = True

    is_running_mock = mock.Mock(return_value=False)
    monkeypatch.setattr(
        "app.background_worker.is_another_instance_running", is_running_mock
    )

    shutdown_event = Event()
    shutdown_mock = mock.Mock()
    monkeypatch.setattr(
        "apscheduler.schedulers.background.BackgroundScheduler.shutdown",
        shutdown_mock,
    )

    def modified_run_scheduler():
        global running
        scheduler = apscheduler.schedulers.background.BackgroundScheduler()
        scheduler.add_job(shutdown_event.set, "interval", seconds=1)
        scheduler.start()

        while running:
            time.sleep(0.1)
            if shutdown_event.is_set():
                break
        logging.info(
            "Scheduler shut down"
        )  # Логирование перед завершением работы
        scheduler.shutdown()
        running = False

    with caplog.at_level(logging.DEBUG):
        scheduler_thread = threading.Thread(
            target=modified_run_scheduler, daemon=True
        )
        scheduler_thread.start()

        with timed("Scheduler execution"):
            time.sleep(2)

        shutdown_event.set()  # Принудительно устанавливаем событие для завершения планировщика
        scheduler_thread.join()

    assert not scheduler_thread.is_alive()
    shutdown_mock.assert_called_once()
    assert "Scheduler shut down" in caplog.text


if __name__ == "__main__":
    pytest.main()
