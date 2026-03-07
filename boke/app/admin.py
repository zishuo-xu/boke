import os
from datetime import datetime
from io import BytesIO
from uuid import uuid4

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from .extensions import db
from .models import Category, MediaAsset, Post, PostDraft, PostVersion, Tag
from .permissions import is_admin_user
from .utils import auto_summary, render_markdown

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
        "media_total": MediaAsset.query.count(),
    }
    latest_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, latest_posts=latest_posts)


@admin_bp.route("/posts")
@login_required
def posts():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "all", type=str)

    query = Post.query
    if status == "published":
        query = query.filter(Post.status == Post.STATUS_PUBLISHED)
    elif status == "draft":
        query = query.filter(Post.status == Post.STATUS_DRAFT)
    elif status == "trash":
        query = query.filter(Post.status == Post.STATUS_TRASH)
    elif status == "all":
        pass
    else:
        status = "all"

    pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template(
        "admin/posts.html", pagination=pagination, posts=pagination.items, status_filter=status
    )


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


def editor_upload_response(success: bool, message: str, url: str = ""):
    return jsonify({"success": 1 if success else 0, "message": message, "url": url})


def normalize_image_and_build_filename(file_storage):
    original_name = secure_filename(file_storage.filename or "image")
    ext = (os.path.splitext(original_name)[1] or "").lower()
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    if ext not in allowed_ext:
        raise ValueError("仅支持 jpg/jpeg/png/webp 格式图片")

    try:
        image = Image.open(file_storage.stream)
    except UnidentifiedImageError as err:
        raise ValueError("无法识别图片文件") from err

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    max_dim = int(current_app.config.get("MEDIA_MAX_DIMENSION", 1920))
    image.thumbnail((max_dim, max_dim))

    uid = uuid4().hex[:16]
    date_path = datetime.now().strftime("%Y/%m")
    save_ext = ".jpg" if ext in {".jpg", ".jpeg"} else ext
    save_name = f"{uid}{save_ext}"
    upload_subdir = current_app.config.get("MEDIA_UPLOAD_SUBDIR", "uploads/media")
    storage_rel_dir = os.path.join(upload_subdir, date_path)
    storage_rel_path = os.path.join(storage_rel_dir, save_name)
    storage_abs_dir = os.path.join(current_app.root_path, "static", storage_rel_dir)
    os.makedirs(storage_abs_dir, exist_ok=True)
    storage_abs_path = os.path.join(storage_abs_dir, save_name)

    output = BytesIO()
    if save_ext == ".png":
        image.save(output, format="PNG", optimize=True)
        mime_type = "image/png"
    elif save_ext == ".webp":
        image.save(output, format="WEBP", quality=82, method=6)
        mime_type = "image/webp"
    else:
        image = image.convert("RGB")
        image.save(
            output,
            format="JPEG",
            quality=int(current_app.config.get("MEDIA_JPEG_QUALITY", 82)),
            optimize=True,
        )
        mime_type = "image/jpeg"

    data = output.getvalue()
    max_bytes = int(current_app.config.get("MEDIA_MAX_BYTES", 5 * 1024 * 1024))
    if len(data) > max_bytes:
        raise ValueError("图片体积过大，请压缩后再上传（<=5MB）")

    with open(storage_abs_path, "wb") as f:
        f.write(data)

    return {
        "filename": save_name,
        "storage_path": storage_rel_path.replace("\\", "/"),
        "mime_type": mime_type,
        "file_size": len(data),
        "width": image.width,
        "height": image.height,
    }


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
        action = request.form.get("action", "draft")
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
            status=Post.STATUS_PUBLISHED if action == "publish" else Post.STATUS_DRAFT,
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
        action = request.form.get("action", "draft")
        post.status = Post.STATUS_PUBLISHED if action == "publish" else Post.STATUS_DRAFT
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
    if post.status == Post.STATUS_TRASH:
        flash("该文章已在回收站", "warning")
        return redirect(url_for("admin.posts", status="trash"))

    snapshot_post(post, current_user.id, "移入回收站前")
    post.status = Post.STATUS_TRASH
    db.session.commit()
    snapshot_post(post, current_user.id, "已移入回收站")
    db.session.commit()
    flash("文章已移入回收站", "info")
    return redirect(url_for("admin.posts"))


@admin_bp.route("/posts/<int:post_id>/restore", methods=["POST"])
@login_required
def post_restore(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.status != Post.STATUS_TRASH:
        flash("仅回收站文章可恢复", "warning")
        return redirect(url_for("admin.posts"))

    snapshot_post(post, current_user.id, "恢复前备份")
    post.status = Post.STATUS_DRAFT
    db.session.commit()
    snapshot_post(post, current_user.id, "已从回收站恢复为草稿")
    db.session.commit()
    flash("文章已恢复为草稿", "success")
    return redirect(url_for("admin.posts", status="trash"))


@admin_bp.route("/posts/<int:post_id>/destroy", methods=["POST"])
@login_required
def post_destroy(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.status != Post.STATUS_TRASH:
        flash("请先将文章移入回收站，再执行彻底删除", "warning")
        return redirect(url_for("admin.posts"))

    PostVersion.query.filter_by(post_id=post.id).delete(synchronize_session=False)
    PostDraft.query.filter_by(post_id=post.id).delete(synchronize_session=False)
    post.tags = []
    db.session.delete(post)
    db.session.commit()
    flash("文章已彻底删除", "info")
    return redirect(url_for("admin.posts", status="trash"))


@admin_bp.route("/media")
@login_required
def media_library():
    page = request.args.get("page", 1, type=int)
    pagination = MediaAsset.query.order_by(MediaAsset.created_at.desc()).paginate(
        page=page, per_page=24, error_out=False
    )
    return render_template(
        "admin/media.html", pagination=pagination, assets=pagination.items
    )


@admin_bp.route("/media/upload", methods=["POST"])
@login_required
def media_upload():
    file_storage = request.files.get("editormd-image-file") or request.files.get("file")
    if not file_storage or not file_storage.filename:
        return editor_upload_response(False, "未检测到上传文件"), 400

    try:
        meta = normalize_image_and_build_filename(file_storage)
    except ValueError as e:
        return editor_upload_response(False, str(e)), 400
    except Exception:
        return editor_upload_response(False, "图片处理失败，请重试"), 500

    asset = MediaAsset(
        uploader_id=current_user.id,
        filename=meta["filename"],
        storage_path=meta["storage_path"],
        mime_type=meta["mime_type"],
        file_size=meta["file_size"],
        width=meta["width"],
        height=meta["height"],
    )
    db.session.add(asset)
    db.session.commit()

    file_url = url_for("static", filename=asset.storage_path)
    return editor_upload_response(True, "上传成功", file_url)


@admin_bp.route("/media/<int:asset_id>/delete", methods=["POST"])
@login_required
def media_delete(asset_id: int):
    asset = MediaAsset.query.get_or_404(asset_id)
    abs_path = os.path.join(current_app.root_path, "static", asset.storage_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)
    db.session.delete(asset)
    db.session.commit()
    flash("图片已删除", "info")
    return redirect(url_for("admin.media_library"))


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


@admin_bp.route("/posts/<int:post_id>/versions/<int:version_id>")
@login_required
def post_version_preview(post_id: int, version_id: int):
    post = Post.query.get_or_404(post_id)
    version = PostVersion.query.filter_by(id=version_id, post_id=post.id).first_or_404()
    rendered_html, toc_html = render_markdown(version.content)
    return render_template(
        "admin/post_version_preview.html",
        post=post,
        version=version,
        rendered_html=rendered_html,
        toc_html=toc_html,
    )


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


@admin_bp.route("/categories/quick-add", methods=["POST"])
@login_required
def category_quick_add():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    sort = data.get("sort", 0)

    if not name:
        return jsonify({"ok": False, "message": "分类名称不能为空"}), 400

    existed = Category.query.filter_by(name=name).first()
    if existed:
        return jsonify(
            {
                "ok": False,
                "message": "分类已存在",
                "category": {"id": existed.id, "name": existed.name},
            }
        ), 409

    try:
        sort_value = int(sort)
    except (TypeError, ValueError):
        sort_value = 0

    category = Category(name=name, sort=sort_value)
    db.session.add(category)
    db.session.commit()
    return jsonify({"ok": True, "category": {"id": category.id, "name": category.name}})


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
