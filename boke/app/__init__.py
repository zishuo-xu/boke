from datetime import timedelta
import os
from flask import Flask, session
from flask_login import current_user

from .admin import admin_bp
from .auth import auth_bp
from .extensions import db, login_manager
from .models import User
from .permissions import is_admin_user
from .public import public_bp


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


def create_app():
    admin_names_raw = os.getenv("ADMIN_USERNAMES", "admin")
    admin_names = {name.strip() for name in admin_names_raw.split(",") if name.strip()} or {"admin"}

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///blog.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        ADMIN_USERNAMES=admin_names,
        MEDIA_UPLOAD_SUBDIR="uploads/media",
        MEDIA_MAX_BYTES=5 * 1024 * 1024,
        MEDIA_MAX_DIMENSION=1920,
        MEDIA_JPEG_QUALITY=82,
    )

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def refresh_session_timeout():
        if "_user_id" in session:
            session.permanent = True
            session.modified = True

    @app.context_processor
    def inject_auth_flags():
        return {
            "is_admin_user": is_admin_user(
                current_user, app.config.get("ADMIN_USERNAMES", {"admin"})
            )
        }

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("数据库初始化完成")

    @app.cli.command("create-admin")
    def create_admin_command():
        username = "admin"
        password = "admin123"
        user = User.query.filter_by(username=username).first()
        if user:
            print("管理员已存在：admin")
            return
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("管理员创建完成：admin / admin123")

    return app
