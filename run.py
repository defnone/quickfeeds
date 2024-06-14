from threading import Thread, Lock
from flask import Flask
from waitress import serve
from app import create_app, db
from app.models import Category, User
from app.background_worker import run_scheduler

app = create_app()
background_worker_started = False
background_worker_lock = Lock()


def start_background_worker():
    """
    Starts the background worker in a new thread if no update thread is
    currently running.
    """
    global background_worker_started
    with background_worker_lock:
        if not background_worker_started:
            thread = Thread(target=run_scheduler, daemon=True)
            thread.start()
            background_worker_started = True


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

    # Uncomment this line to use Waitress for serving the application
    serve(app, host=app.config["FLASK_HOST"], port=app.config["FLASK_PORT"])

    # Comment this line if you are using Waitress
    # app.run(debug=True, port=8000, host="0.0.0.0")
