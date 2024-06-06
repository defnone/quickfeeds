from flask_login import UserMixin
from werkzeug.security import check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    feeds = db.relationship("Feed", backref="user", lazy=True)
    last_sync = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_category_user", ondelete="CASCADE"),
    )
    feeds = db.relationship("Feed", backref="category", lazy=True)

    def __repr__(self):
        return f"Category('{self.name}')"


db.Index("index_category_user_id", Category.user_id)


class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(200), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("category.id"), nullable=True
    )
    items = db.relationship(
        "FeedItem", backref="feed", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
        }


db.Index("index_feed_user_id", Feed.user_id)
db.Index("index_feed_category_id", Feed.category_id)


class FeedItem(db.Model):
    """
    Represents a feed item.

    This class is used to store and manipulate feed items.
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(200), unique=True, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    pub_date = db.Column(db.DateTime, nullable=True, index=True)
    creator = db.Column(db.String(200), nullable=True)
    read = db.Column(db.Boolean, default=False, nullable=False)
    favourite = db.Column(db.Boolean, default=False, nullable=False)
    guid = db.Column(db.String(500))
    feed_id = db.Column(db.Integer, db.ForeignKey("feed.id"), nullable=False)

    def to_dict(self):
        """
        Converts the object to a dictionary.

        Returns:
            dict: A dictionary representation of the object.
        """
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "pub_date": self.pub_date.isoformat() if self.pub_date else None,
            "creator": self.creator,
            "read": self.read,
            "guid": self.guid,
            "feed_id": self.feed_id,
        }


db.Index("index_feed_item_feed_id", FeedItem.feed_id)


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    update_interval = db.Column(db.Integer, nullable=False, default=60)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timezone = db.Column(db.String(50), nullable=False, default="UTC")
    language = db.Column(db.String(50), nullable=False, default="English")
    unread = db.Column(db.Boolean, nullable=False, default=True)
    groq_api_key = db.Column(db.String(100), nullable=True)
    translate = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship(
        "User", backref=db.backref("settings", uselist=False)
    )
