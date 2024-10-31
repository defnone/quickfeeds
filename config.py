import os
from datetime import timedelta
from app.utils.secret_key import secret_key


class Config:
    SECRET_KEY = secret_key()
    SQLALCHEMY_DATABASE_URI = "sqlite:///main.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    FLASK_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_RUN_PORT", 8000))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False")


class TestingConfig(Config):
    TESTING = True
    FLASK_HOST = "localhost"
    FLASK_PORT = 5000
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "default_secret_key"
    LOG_LEVEL = "DEBUG"
    LOG_FILE = "logs/debug_app.log"
