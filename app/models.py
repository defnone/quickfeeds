from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    """
    Represents a user in the application.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): The username chosen by the user.
        password (str): The user's password (hashed for security).
        feeds (db.relationship): A list of Feed objects associated with the
        user.
        last_sync (datetime): The last time the user's feeds were synchronized.
        daily_sync_at (datetime): The scheduled time for the Daily feed
        synchronization.

    Methods:
        __repr__ (): Returns a string representation of the user.
        check_password (str): Verifies the user's password.

    Relationships:
        user (Feed): The Feed objects associated with this user.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    feeds = db.relationship("Feed", backref="user", lazy=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    daily_sync_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        """Returns a string representation of the user."""
        return f"<User {self.username}>"

    def check_password(self, password):
        """Verifies the user's password."""
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

    def to_dict(self):
        return {"id": self.id, "name": self.name, "user_id": self.user_id}


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
    daily_enabled = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "daily_enabled": self.daily_enabled,
        }


db.Index("index_feed_user_id", Feed.user_id)
db.Index("index_feed_category_id", Feed.category_id)


class FeedItem(db.Model):
    """
    Represents a single feed item in the application.

    Attributes:
        id (int): Unique identifier for the feed item.
        title (str): The title of the feed item.
        link (str): The URL of the feed item.
        summary (str): A brief summary of the feed item.
        pub_date (datetime): The publication date of the feed item.
        creator (str): The creator of the feed item.
        read (bool): Whether the feed item has been read.
        favourite (bool): Whether the feed item is a favourite.
        guid (str): A globally unique identifier for the feed item.
        feed_id (int): Foreign key referencing the Feed model.

    Relationships:
        summarized_articles (ArticleLink): A list of summarized articles linked to this feed item.

    Methods:
        to_dict (): Converts the object to a dictionary representation.
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
    summarized_articles = db.relationship(
        "ArticleLink",
        back_populates="original_article",
        cascade="all, delete-orphan",
    )

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
db.Index("index_feed_item_read", FeedItem.read)


class SummarizedArticle(db.Model):
    """
    Represents a summarized article in the application.

    Attributes:
        id (int): Unique identifier for the summarized article.
        summary (str): The summary content of the article.
        link (str): A unique URL link to the summarized article.
        created_at (datetime): The timestamp when the summarized article was
        created, defaulting to the current time in UTC timezone.
        image_link (str): A URL link to an image associated with the summarized
        article, if available.
        read (bool): Indicates whether the summarized article has been read
        by the user.

    Relationships:
        original_articles (ArticleLink): A list of ArticleLink instances
        linking this summarized article to its original articles.
    """

    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.Text)
    link = db.Column(db.String, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    image_link = db.Column(db.String, nullable=True)
    read = db.Column(db.Boolean, default=False, nullable=False)
    original_articles = db.relationship(
        "ArticleLink", back_populates="summarized_article"
    )


class ArticleLink(db.Model):
    """
    Represents a link between a summarized article and its original article
    in the application.

    Attributes:
        id (int): Unique identifier for the ArticleLink.
        original_article_id (int): Foreign key referencing the original
            article in the FeedItem model.
        summarized_article_id (int): Foreign key referencing the summarized
            article in the SummarizedArticle model.
        summarized_article (SummarizedArticle): The summarized article
            associated with this link.
        original_article (FeedItem): The original article linked to this
            summarized article.

    Relationships:
        original_article (FeedItem): The FeedItem instance that is the
            original article.
        summarized_article (SummarizedArticle): The SummarizedArticle
            instance that is the summarized version of the original article.
    """

    id = db.Column(db.Integer, primary_key=True)
    original_article_id = db.Column(
        db.Integer, db.ForeignKey("feed_item.id"), nullable=False
    )
    summarized_article_id = db.Column(
        db.Integer, db.ForeignKey("summarized_article.id"), nullable=False
    )
    summarized_article = db.relationship(
        "SummarizedArticle", back_populates="original_articles"
    )
    original_article = db.relationship(
        "FeedItem", back_populates="summarized_articles"
    )


class Settings(db.Model):
    """
    Represents a user's settings in the application.

    Attributes:
        id (int): Unique identifier for the settings record.
        update_interval (int): The frequency at which the user's
            feeds are updated.
        clean_after_days (int): The number of days after which unread
            items are cleaned up.
        user_id (int): Foreign key referencing the User model.
        timezone (str): The user's preferred timezone.
        language (str): The user's preferred language.
        unread (bool): Whether to display unread items or all items on pages.
        groq_api_key (str): The user's Groq API key.
        translate (bool): Whether to translate feed items.
        daily_active (bool): Whether daily processing is active.
        daily_hours_summary (int): The hour of the day for daily summaries.
        daily_translate (bool): Whether to translate daily summaries.
        daily_last_sync_time_duration (int): The duration of
            the last daily sync.
        daily_process_read (bool): Whether to process read items daily.

    Relationships:
        user (User): The User instance associated with these settings.

    Methods:
        __str__ (): Returns a string representation of the settings record.
    """

    id = db.Column(db.Integer, primary_key=True)
    update_interval = db.Column(db.Integer, nullable=False, default=60)
    clean_after_days = db.Column(db.Integer, nullable=False, default=60)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timezone = db.Column(db.String(50), nullable=False, default="UTC")
    language = db.Column(db.String(50), nullable=False, default="English")
    unread = db.Column(db.Boolean, nullable=False, default=True)
    groq_api_key = db.Column(db.String(100), nullable=True)
    openai_api_key = db.Column(db.String(100), nullable=True)
    translate = db.Column(db.Boolean, nullable=False, default=False)
    daily_active = db.Column(db.Boolean, nullable=False, default=False)
    daily_hours_summary = db.Column(db.Integer, nullable=False, default=24)
    daily_translate = db.Column(db.Boolean, nullable=False, default=False)
    daily_last_sync_time_duration = db.Column(db.Integer, nullable=True)
    daily_process_read = db.Column(db.Boolean, nullable=False, default=False)
    daily_title_provider = db.Column(
        db.String(50), nullable=False, default="groq"
    )
    daily_compare_titles = db.Column(db.Boolean, nullable=False, default=True)

    # Relationship with User model through the `user` attribute.
    user = db.relationship(
        "User", backref=db.backref("settings", uselist=False)
    )

    def __str__(self) -> str:
        """
        String representation of a Settings instance.

        Returns:
            A string describing the `id` and associated `user_id` of the
            settings record.
        """
        return f"Settings(id={self.id}, user_id={self.user_id})"
