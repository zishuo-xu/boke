from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from .models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("用户名或密码错误", "danger")
            return render_template("auth_login.html")

        login_user(user)
        session.permanent = True
        session.modified = True
        return redirect(request.args.get("next") or url_for("admin.dashboard"))

    return render_template("auth_login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("已退出登录", "info")
    return redirect(url_for("public.home"))


@auth_bp.app_context_processor
def inject_session_timeout():
    return {"session_timeout_minutes": int(timedelta(hours=1).total_seconds() / 60)}
