from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for,
    flash,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User, Settings

auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if User.query.first():
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        settings = Settings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        login_user(user)
        return redirect(url_for("routes.index"))
    return render_template("register.html", title="First Run")


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.index"))
    if not User.query.first():
        return redirect(url_for("auth.register"))
    if request.method == "POST":
        username = request.form["login"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            login_user(user, remember=True)
            session.permanent = True
            flash(("You have logged in", "success"))
            return redirect(url_for("routes.index"))
        flash(("Invalid login or password", "error"))
        return redirect(url_for("auth.login"))
    return render_template("login.html", title="Login to QuickFeeds")


@auth_blueprint.route("/logout")
@login_required
def logout():
    session.clear()
    logout_user()
    flash(("You have logged out", "success"))
    return redirect(url_for("auth.login"))
