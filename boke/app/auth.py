from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from .extensions import db
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


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3:
            flash("用户名至少 3 个字符", "danger")
            return render_template("auth_register.html")
        if len(password) < 6:
            flash("密码至少 6 位", "danger")
            return render_template("auth_register.html")
        if password != confirm_password:
            flash("两次输入的密码不一致", "danger")
            return render_template("auth_register.html")
        if User.query.filter_by(username=username).first():
            flash("用户名已存在，请更换", "danger")
            return render_template("auth_register.html")

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        session.permanent = True
        session.modified = True
        flash("注册成功，已自动登录", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("auth_register.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("已退出登录", "info")
    return redirect(url_for("public.home"))


@auth_bp.app_context_processor
def inject_session_timeout():
    return {"session_timeout_minutes": int(timedelta(hours=1).total_seconds() / 60)}
