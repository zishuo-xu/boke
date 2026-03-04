from datetime import timedelta

from flask import Flask, session

from .admin import admin_bp
from .auth import auth_bp
from .extensions import db, login_manager
from .models import User
from .public import public_bp


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev-secret-key-change-me",
        SQLALCHEMY_DATABASE_URI="sqlite:///blog.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
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
