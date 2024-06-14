from threading import Thread
from flask import g
from waitress import serve
from app import create_app, db
from app.models import Category, User
from app.background_worker import run_scheduler

app = create_app()


def start_background_worker():
    """
    Starts the background worker in a new thread if no update thread is
    currently running.

    If the global variable `g.update_thread` does not exist or is not alive, a
    new thread is created using the `run_scheduler` function as the
    target. The new thread is started as a daemon thread.
    """
    if (
        not hasattr(g, "background_thread")
        or not g.background_thread.is_alive()
    ):
        g.background_thread = Thread(target=run_scheduler, daemon=True)
        g.background_thread.start()


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
    serve(app, host=app.config["FLASK_HOST"], port=app.config["FLASK_PORT"])
    # app.run(debug=True, port=8000, host="0.0.0.0")
