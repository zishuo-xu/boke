from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


post_tag = db.Table(
    "post_tag",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Category(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    sort = db.Column(db.Integer, default=0, nullable=False)

    posts = db.relationship("Post", back_populates="category", lazy="dynamic")


class Tag(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)


class Post(TimestampMixin, db.Model):
    STATUS_DRAFT = 0
    STATUS_PUBLISHED = 1
    STATUS_TRASH = 2

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500), nullable=False, default="")
    status = db.Column(db.Integer, nullable=False, default=STATUS_DRAFT)
    view_count = db.Column(db.Integer, default=0, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), index=True)
    category = db.relationship("Category", back_populates="posts")

    tags = db.relationship("Tag", secondary=post_tag, lazy="subquery", backref="posts")

    @property
    def is_published(self) -> bool:
        return self.status == self.STATUS_PUBLISHED


class PostVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    editor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500), nullable=False, default="")
    status = db.Column(db.Integer, nullable=False, default=Post.STATUS_DRAFT)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), index=True)
    tags_text = db.Column(db.String(500), nullable=False, default="")
    version_note = db.Column(db.String(120), nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    post = db.relationship("Post", backref="versions")
    editor = db.relationship("User")
    category = db.relationship("Category")


class PostDraft(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True, index=True)
    draft_key = db.Column(db.String(64), nullable=True, index=True)

    title = db.Column(db.String(100), nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    summary = db.Column(db.String(500), nullable=False, default="")
    status = db.Column(db.Integer, nullable=False, default=Post.STATUS_DRAFT)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), index=True)
    tags_text = db.Column(db.String(500), nullable=False, default="")

    user = db.relationship("User")
    post = db.relationship("Post")
    category = db.relationship("Category")


class MediaAsset(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False, unique=True)
    mime_type = db.Column(db.String(100), nullable=False, default="")
    file_size = db.Column(db.Integer, nullable=False, default=0)
    width = db.Column(db.Integer, nullable=False, default=0)
    height = db.Column(db.Integer, nullable=False, default=0)

    uploader = db.relationship("User")


class Comment(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)

    post = db.relationship("Post", backref="comments")
    user = db.relationship("User")
