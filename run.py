from threading import Thread, Lock
from flask import send_from_directory
from waitress import serve
from app import create_app, db
from app.models import Category, User
from app.background_worker import run_scheduler

app = create_app()
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
        db.create_all()
        # Check if category "Unnamed" exists
        user = User.query.first()
        if user:
            category = Category.query.filter_by(name="Unnamed").first()
            if not category:
                # Create category "Unnamed"
                category = Category(name="Unnamed", user_id=user.id)
                db.session.add(category)
                db.session.commit()
        # Start the background worker
        start_background_worker()

    # Waitress is used as the production server
    serve(app, host=app.config["FLASK_HOST"], port=app.config["FLASK_PORT"])

    # Use the following line to run the app using Flask's development server
    # app.run(debug=True, port=8000, host="0.0.0.0")
