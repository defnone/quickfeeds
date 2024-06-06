"""
This script allows you to change the password of a user in your application.

It uses the argparse module to parse command line arguments, the
werkzeug.security module to generate a hashed password, and the app and User
models from your application.

The script defines a function change_password that takes a username and a new
password as arguments. It queries the database for the user with the given
username, and if it finds one, it changes the user's password to the hashed
version of the new password and commits the changes to the database. If it
doesn't find a user with the given username, it prints a message saying that
the user was not found.

The script then defines a command line argument parser that expects a username
and a new password as arguments. It parses the command line arguments and calls
the change_password function with the parsed arguments.

You can run this script from the command line like this:

python change_password.py username new_password

where username is the username of the user whose password you want to change,
and new_password is the new password you want to set for the user.
"""

import argparse
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User

app = create_app()


def change_password(username, new_password):
    """
    Change the password of a user.

    This function queries the database for a user with the given username. If
    it finds one, it changes the user's password to the hashed version of the
    new password and commits the changes to the database. If it doesn't find a
    user with the given username, it prints a message saying that the user was
    not found.

    Args:
        username (str): The username of the user whose password you want to
        change. new_password (str): The new password you want to set for the
        user.
    """
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            print(f"Password for user {username} has been changed.")
        else:
            print(f"User {username} not found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change user password.")
    parser.add_argument("username", type=str, help="Username")
    parser.add_argument("new_password", type=str, help="New password")
    args = parser.parse_args()

    change_password(args.username, args.new_password)
