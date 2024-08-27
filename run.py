import os
from threading import Thread, Lock
from flask import send_from_directory
from waitress import serve
from app import create_app, db
from app.models import Category, User
from app.background_worker import run_scheduler

config_name = os.getenv("FLASK_CONFIG", "default")
app = create_app(config_name)

BACKGROUND_WORKER_STARTED = False
BACKGROUND_WORKER_LOCK = Lock()


def start_background_worker():
    """
    Starts the background worker in a new thread if no background worker is
    currently running.
    """

    global BACKGROUND_WORKER_STARTED
    with BACKGROUND_WORKER_LOCK:
        if not BACKGROUND_WORKER_STARTED:
            thread = Thread(target=run_scheduler, daemon=True)
            thread.start()
            BACKGROUND_WORKER_STARTED = True


@app.route("/robots.txt")
def robots_txt():
    """Returns the robots.txt file from app/static"""
    return send_from_directory(app.static_folder, "robots.txt")


if __name__ == "__main__":
    with app.app_context():
        if config_name == "testing":
            db.drop_all()
        db.create_all()
        # Check if category "Unnamed" exists
        user = User.query.first()
        if user:
            category = Category.query.filter_by(name="Unnamed").first()
            start_background_worker()
            if not category:
                # Create category "Unnamed"
                category = Category(name="Unnamed", user_id=user.id)
                db.session.add(category)
                db.session.commit()

    if os.getenv("ENV"):
        if os.getenv("ENV") == "DEV":
            app.run(debug=True, port=8000, host="0.0.0.0", use_reloader=False)
    else:
        serve(
            app,
            host=app.config["FLASK_HOST"],
            port=app.config["FLASK_PORT"],
        )
