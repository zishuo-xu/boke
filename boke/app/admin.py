from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user

from .extensions import db
from .models import Category, Post, PostDraft, PostVersion, Tag
from .permissions import is_admin_user
from .utils import auto_summary

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def require_admin_login():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))
    if not is_admin_user(current_user, current_app.config.get("ADMIN_USERNAMES", {"admin"})):
        logout_user()
        flash("无后台管理权限，请使用管理员账号登录。", "warning")
        return redirect(url_for("auth.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "post_total": Post.query.count(),
        "category_total": Category.query.count(),
        "tag_total": Tag.query.count(),
    }
    latest_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, latest_posts=latest_posts)


@admin_bp.route("/posts")
@login_required
def posts():
    page = request.args.get("page", 1, type=int)
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template("admin/posts.html", pagination=pagination, posts=pagination.items)


def parse_tags(raw_tags: str):
    names = [name.strip() for name in (raw_tags or "").split(",") if name.strip()]
    unique_names = list(dict.fromkeys(names))
    tags = []
    for name in unique_names:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def snapshot_post(post: Post, editor_id: int, note: str) -> None:
    version = PostVersion(
        post_id=post.id,
        editor_id=editor_id,
        title=post.title,
        content=post.content,
        summary=post.summary,
        status=post.status,
        category_id=post.category_id,
        tags_text=", ".join([t.name for t in post.tags]),
        version_note=note,
    )
    db.session.add(version)


def get_draft_for_form(post_id: int | None, draft_key: str) -> PostDraft | None:
    query = PostDraft.query.filter_by(user_id=current_user.id)
    if post_id:
        return query.filter_by(post_id=post_id).first()
    if draft_key:
        return query.filter_by(draft_key=draft_key).first()
    return None


@admin_bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def post_new():
    categories = Category.query.order_by(Category.sort.asc(), Category.id.asc()).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        summary = request.form.get("summary", "").strip()
        status = request.form.get("status", "0")
        category_id = request.form.get("category_id", type=int)
        raw_tags = request.form.get("tags", "")

        if not title or not content:
            flash("标题和内容不能为空", "danger")
            return render_template(
                "admin/post_form.html",
                categories=categories,
                versions=[],
            )

        post = Post(
            title=title,
            content=content,
            summary=summary or auto_summary(content),
            status=Post.STATUS_PUBLISHED if status == "1" else Post.STATUS_DRAFT,
            category_id=category_id,
        )
        post.tags = parse_tags(raw_tags)

        db.session.add(post)
        db.session.commit()
        snapshot_post(post, current_user.id, "初始创建")
        db.session.commit()
        flash("文章已创建", "success")
        return redirect(url_for("admin.posts"))

    return render_template(
        "admin/post_form.html",
        categories=categories,
        versions=[],
    )


@admin_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def post_edit(post_id: int):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.order_by(Category.sort.asc(), Category.id.asc()).all()
    versions = (
        PostVersion.query.filter_by(post_id=post.id)
        .order_by(PostVersion.created_at.desc(), PostVersion.id.desc())
        .limit(20)
        .all()
    )
    draft = get_draft_for_form(post_id=post.id, draft_key="")

    if request.method == "POST":
        snapshot_post(post, current_user.id, "手动保存前")
        post.title = request.form.get("title", "").strip()
        post.content = request.form.get("content", "").strip()
        post.summary = request.form.get("summary", "").strip() or auto_summary(post.content)
        post.status = (
            Post.STATUS_PUBLISHED if request.form.get("status", "0") == "1" else Post.STATUS_DRAFT
        )
        post.category_id = request.form.get("category_id", type=int)
        post.tags = parse_tags(request.form.get("tags", ""))

        if not post.title or not post.content:
            flash("标题和内容不能为空", "danger")
            return render_template(
                "admin/post_form.html",
                post=post,
                categories=categories,
                versions=versions,
            )

        db.session.commit()
        snapshot_post(post, current_user.id, "手动保存后")
        draft = get_draft_for_form(post_id=post.id, draft_key="")
        if draft:
            db.session.delete(draft)
            db.session.commit()
        flash("文章已更新", "success")
        return redirect(url_for("admin.posts"))

    raw_tags = ", ".join([tag.name for tag in post.tags])
    if draft:
        flash("检测到自动保存草稿，已优先载入草稿内容", "info")
    return render_template(
        "admin/post_form.html",
        post=post,
        categories=categories,
        raw_tags=raw_tags,
        draft=draft,
        versions=versions,
    )


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def post_delete(post_id: int):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("文章已删除", "info")
    return redirect(url_for("admin.posts"))


@admin_bp.route("/posts/autosave", methods=["POST"])
@login_required
def post_autosave():
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    if not post_id:
        return jsonify({"ok": False, "message": "new_post_skip"}), 200

    query = PostDraft.query.filter_by(user_id=current_user.id)
    draft = None
    draft = query.filter_by(post_id=int(post_id)).first()

    if not draft:
        draft = PostDraft(
            user_id=current_user.id,
            post_id=int(post_id),
            draft_key=None,
        )
        db.session.add(draft)

    draft.title = (data.get("title") or "").strip()
    draft.content = data.get("content") or ""
    draft.summary = (data.get("summary") or "").strip()
    draft.status = Post.STATUS_PUBLISHED if str(data.get("status", "0")) == "1" else Post.STATUS_DRAFT
    draft.category_id = int(data["category_id"]) if data.get("category_id") else None
    draft.tags_text = (data.get("tags") or "").strip()

    db.session.commit()
    return jsonify({"ok": True, "updated_at": draft.updated_at.isoformat()})


@admin_bp.route("/posts/<int:post_id>/rollback/<int:version_id>", methods=["POST"])
@login_required
def post_rollback(post_id: int, version_id: int):
    post = Post.query.get_or_404(post_id)
    version = PostVersion.query.filter_by(id=version_id, post_id=post.id).first_or_404()

    snapshot_post(post, current_user.id, f"回滚前备份 v{version.id}")
    post.title = version.title
    post.content = version.content
    post.summary = version.summary
    post.status = version.status
    post.category_id = version.category_id
    post.tags = parse_tags(version.tags_text)
    db.session.commit()
    snapshot_post(post, current_user.id, f"已回滚到 v{version.id}")
    db.session.commit()

    flash(f"已回滚到版本 #{version.id}", "success")
    return redirect(url_for("admin.post_edit", post_id=post.id))


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sort = request.form.get("sort", 0, type=int)
        if not name:
            flash("分类名称不能为空", "danger")
        elif Category.query.filter_by(name=name).first():
            flash("分类已存在", "danger")
        else:
            db.session.add(Category(name=name, sort=sort))
            db.session.commit()
            flash("分类已新增", "success")
        return redirect(url_for("admin.categories"))

    categories_list = Category.query.order_by(Category.sort.asc(), Category.id.asc()).all()
    return render_template("admin/categories.html", categories=categories_list)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def category_delete(category_id: int):
    category = Category.query.get_or_404(category_id)
    if category.posts.count() > 0:
        flash("分类下仍有文章，无法删除", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("分类已删除", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/tags", methods=["GET", "POST"])
@login_required
def tags():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("标签名称不能为空", "danger")
        elif Tag.query.filter_by(name=name).first():
            flash("标签已存在", "danger")
        else:
            db.session.add(Tag(name=name))
            db.session.commit()
            flash("标签已新增", "success")
        return redirect(url_for("admin.tags"))

    tags_list = Tag.query.order_by(Tag.name.asc()).all()
    return render_template("admin/tags.html", tags=tags_list)


@admin_bp.route("/tags/delete", methods=["POST"])
@login_required
def tags_delete_batch():
    ids = request.form.getlist("tag_ids")
    if not ids:
        flash("请先选择要删除的标签", "warning")
        return redirect(url_for("admin.tags"))

    for tag_id in ids:
        tag = Tag.query.get(int(tag_id))
        if tag:
            tag.posts = []
            db.session.delete(tag)
    db.session.commit()
    flash("标签已批量删除", "info")
    return redirect(url_for("admin.tags"))


@admin_bp.route("/tags/merge", methods=["POST"])
@login_required
def tags_merge():
    source_id = request.form.get("source_id", type=int)
    target_id = request.form.get("target_id", type=int)

    if not source_id or not target_id or source_id == target_id:
        flash("请选择两个不同标签进行合并", "danger")
        return redirect(url_for("admin.tags"))

    source = Tag.query.get_or_404(source_id)
    target = Tag.query.get_or_404(target_id)

    for post in source.posts:
        if target not in post.tags:
            post.tags.append(target)
    source.posts = []
    db.session.delete(source)
    db.session.commit()

    flash("标签合并完成", "success")
    return redirect(url_for("admin.tags"))
