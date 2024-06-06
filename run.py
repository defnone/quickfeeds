from threading import Thread
from flask import g
from waitress import serve
from app import create_app, db
from app.models import Category, User
from app.feed_updater import update_feeds_thread

app = create_app()


def update_feeds():
    """
    Starts a new thread to update feeds if no update thread is currently
    running.

    If the global variable `g.update_thread` does not exist or is not alive, a
    new thread is created using the `update_feeds_thread` function as the
    target. The new thread is started as a daemon thread.

    Note:
        The `g` object is assumed to be a global object that holds shared data
        across the application.

    """
    if not hasattr(g, "update_thread") or not g.update_thread.is_alive():
        g.update_thread = Thread(target=update_feeds_thread, daemon=True)
        g.update_thread.start()


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
        # Start the feed update thread
        update_feeds()
    serve(app, host=app.config["FLASK_HOST"], port=app.config["FLASK_PORT"])
    # app.run(debug=True, port=8000, host="0.0.0.0")
