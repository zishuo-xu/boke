#!/usr/bin/env sh
set -e

flask --app run.py init-db

python - <<'PY'
import os
from app import create_app
from app.extensions import db
from app.models import User

username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
password = os.getenv("ADMIN_PASSWORD", "admin123")

app = create_app()
with app.app_context():
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"管理员创建完成: {username}")
    else:
        print(f"管理员已存在: {username}")
PY

exec gunicorn -b 0.0.0.0:5000 run:app --workers=2 --threads=4 --timeout=60
