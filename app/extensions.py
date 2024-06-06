from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate


def add_trailing_slash(value):
    if not value.endswith("/"):
        return value + "/"
    return value


app = Flask(__name__)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
