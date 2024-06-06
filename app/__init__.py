from flask import Flask
from app.utils.filters import (
    add_trailing_slash,
)
from .extensions import db, migrate, login_manager
from .api.v1.feeditems import api_feeditems_blueprint
from .api.v1.feeds import api_feeds_blueprint
from .api.v1.api_info import api_ui_info_blueprint
from .api.v1.settings import api_settings_blueprint
from .api.v1.summarize import api_summarize_blueprint
from .api.v1.groq import api_groq_blueprint
from .routes.routes import routes_blueprint
from .routes.add_feed import add_feed_blueprint
from .routes.mark_as_read import mark_as_read_blueprint
from .routes.auth import auth_blueprint
from .models import User
import logging_config


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name == "testing":
        app.config.from_object("config.TestingConfig")
    else:
        app.config.from_object("config.Config")

    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    log_file = app.config.get("LOG_FILE", "logs/app.log")
    logging_config.setup_logging(log_level, log_file)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.jinja_env.filters["add_trailing_slash"] = add_trailing_slash

    # Blueprints

    # API UI Info Blueprint
    # This blueprint is responsible for providing UI related information
    # through API endpoints.
    app.register_blueprint(api_ui_info_blueprint, url_prefix="/api")

    # API Feeds Blueprint This blueprint is responsible for handling operations
    # related to feeds through API endpoints.
    app.register_blueprint(api_feeds_blueprint, url_prefix="/api/feeds")

    # API Feed Items Blueprint This blueprint is responsible for handling
    # operations related to feed items through API endpoints.
    app.register_blueprint(
        api_feeditems_blueprint, url_prefix="/api/feeditems"
    )

    # API Settings Blueprint This blueprint is responsible for handling
    # operations related to application settings through API endpoints.
    app.register_blueprint(api_settings_blueprint, url_prefix="/api/settings")

    # API Summarize Blueprint This blueprint is responsible for providing
    # summarization services through API endpoints.
    app.register_blueprint(
        api_summarize_blueprint, url_prefix="/api/summarize"
    )

    # API GROQ Blueprint This blueprint is responsible for handling GROQ
    # operations through API endpoints.
    app.register_blueprint(api_groq_blueprint, url_prefix="/api/groq")

    # Routes Blueprint This blueprint is responsible for handling the main
    # routes of the application.
    app.register_blueprint(routes_blueprint)

    # Add Feed Blueprint This blueprint is responsible for handling operations
    # related to adding new feeds.
    app.register_blueprint(add_feed_blueprint)

    # Mark As Read Blueprint This blueprint is responsible for handling
    # operations related to marking feed items as read.
    app.register_blueprint(mark_as_read_blueprint)

    # Auth Blueprint This blueprint is responsible for handling authentication
    # operations.
    app.register_blueprint(auth_blueprint)

    return app
