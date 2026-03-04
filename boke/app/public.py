from sqlalchemy import func, or_
from flask import Blueprint, abort, render_template, request
from flask_login import current_user

from .extensions import db
from .models import Category, Post, Tag
from .utils import highlight_keyword, match_score, render_markdown

public_bp = Blueprint("public", __name__)


def get_sidebar_data():
    latest_posts = (
        Post.query.filter_by(status=Post.STATUS_PUBLISHED)
        .order_by(Post.created_at.desc())
        .limit(5)
        .all()
    )

    category_stats = (
        db.session.query(Category, func.count(Post.id).label("count"))
        .outerjoin(Post, (Post.category_id == Category.id) & (Post.status == Post.STATUS_PUBLISHED))
        .group_by(Category.id)
        .order_by(Category.sort.asc(), Category.id.asc())
        .all()
    )

    tag_stats = (
        db.session.query(Tag, func.count(Post.id).label("count"))
        .outerjoin(Tag.posts)
        .filter(or_(Post.id.is_(None), Post.status == Post.STATUS_PUBLISHED))
        .group_by(Tag.id)
        .order_by(func.count(Post.id).desc(), Tag.name.asc())
        .all()
    )
    return latest_posts, category_stats, tag_stats


@public_bp.route("/")
def home():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    pagination = (
        Post.query.filter_by(status=Post.STATUS_PUBLISHED)
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=max(1, min(per_page, 30)), error_out=False)
    )
    latest_posts, category_stats, tag_stats = get_sidebar_data()
    return render_template(
        "home.html",
        pagination=pagination,
        posts=pagination.items,
        latest_posts=latest_posts,
        category_stats=category_stats,
        tag_stats=tag_stats,
    )


@public_bp.route("/post/<int:post_id>")
def post_detail(post_id: int):
    post = Post.query.get_or_404(post_id)
    if not post.is_published and not current_user.is_authenticated:
        abort(404)

    post.view_count += 1
    db.session.commit()

    rendered_html, toc_html = render_markdown(post.content)

    prev_post = (
        Post.query.filter(Post.status == Post.STATUS_PUBLISHED, Post.created_at < post.created_at)
        .order_by(Post.created_at.desc())
        .first()
    )
    next_post = (
        Post.query.filter(Post.status == Post.STATUS_PUBLISHED, Post.created_at > post.created_at)
        .order_by(Post.created_at.asc())
        .first()
    )

    latest_posts, category_stats, tag_stats = get_sidebar_data()
    return render_template(
        "post_detail.html",
        post=post,
        rendered_html=rendered_html,
        toc_html=toc_html,
        prev_post=prev_post,
        next_post=next_post,
        latest_posts=latest_posts,
        category_stats=category_stats,
        tag_stats=tag_stats,
    )


@public_bp.route("/search")
def search():
    keyword = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = Post.query.filter_by(status=Post.STATUS_PUBLISHED)
    if keyword:
        query = query.filter(
            or_(
                Post.title.ilike(f"%{keyword}%"),
                Post.summary.ilike(f"%{keyword}%"),
                Post.content.ilike(f"%{keyword}%"),
            )
        )

    posts = query.all()
    scored = sorted(
        posts,
        key=lambda x: (
            match_score(x.title, keyword) * 3
            + match_score(x.summary, keyword) * 2
            + match_score(x.content, keyword)
        ),
        reverse=True,
    )

    start = (page - 1) * per_page
    end = start + per_page
    page_items = scored[start:end]

    highlighted = [
        {
            "post": p,
            "title": highlight_keyword(p.title, keyword),
            "summary": highlight_keyword(p.summary, keyword),
        }
        for p in page_items
    ]

    total = len(scored)
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    latest_posts, category_stats, tag_stats = get_sidebar_data()
    return render_template(
        "search.html",
        keyword=keyword,
        items=highlighted,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        latest_posts=latest_posts,
        category_stats=category_stats,
        tag_stats=tag_stats,
    )


@public_bp.route("/categories")
def categories():
    category_stats = (
        db.session.query(Category, func.count(Post.id).label("count"))
        .outerjoin(Post, (Post.category_id == Category.id) & (Post.status == Post.STATUS_PUBLISHED))
        .group_by(Category.id)
        .order_by(Category.sort.asc(), Category.id.asc())
        .all()
    )
    latest_posts, _, tag_stats = get_sidebar_data()
    return render_template(
        "categories.html",
        category_stats=category_stats,
        latest_posts=latest_posts,
        tag_stats=tag_stats,
    )


@public_bp.route("/category/<int:category_id>")
def category_posts(category_id: int):
    category = Category.query.get_or_404(category_id)
    page = request.args.get("page", 1, type=int)
    pagination = (
        Post.query.filter_by(status=Post.STATUS_PUBLISHED, category_id=category.id)
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    latest_posts, category_stats, tag_stats = get_sidebar_data()
    return render_template(
        "home.html",
        pagination=pagination,
        posts=pagination.items,
        latest_posts=latest_posts,
        category_stats=category_stats,
        tag_stats=tag_stats,
        list_title=f"分类：{category.name}",
    )


@public_bp.route("/tags")
def tags():
    tag_stats = (
        db.session.query(Tag, func.count(Post.id).label("count"))
        .outerjoin(Tag.posts)
        .filter(or_(Post.id.is_(None), Post.status == Post.STATUS_PUBLISHED))
        .group_by(Tag.id)
        .order_by(func.count(Post.id).desc(), Tag.name.asc())
        .all()
    )
    latest_posts, category_stats, _ = get_sidebar_data()
    max_count = max((count for _, count in tag_stats), default=1)

    return render_template(
        "tags.html",
        tag_stats=tag_stats,
        max_count=max_count,
        latest_posts=latest_posts,
        category_stats=category_stats,
    )


@public_bp.route("/tag/<int:tag_id>")
def tag_posts(tag_id: int):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get("page", 1, type=int)

    pagination = (
        Post.query.join(Post.tags)
        .filter(Tag.id == tag.id, Post.status == Post.STATUS_PUBLISHED)
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    latest_posts, category_stats, tag_stats = get_sidebar_data()
    return render_template(
        "home.html",
        pagination=pagination,
        posts=pagination.items,
        latest_posts=latest_posts,
        category_stats=category_stats,
        tag_stats=tag_stats,
        list_title=f"标签：{tag.name}",
    )
