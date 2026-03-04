import re

import bleach
import markdown

ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union(
    {
        "p",
        "pre",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "img",
        "span",
        "div",
        "hr",
    }
)
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "name", "target"],
    "img": ["src", "alt", "title"],
    "code": ["class"],
    "span": ["class"],
    "div": ["class"],
    "h1": ["id"],
    "h2": ["id"],
    "h3": ["id"],
    "h4": ["id"],
    "h5": ["id"],
    "h6": ["id"],
}


def render_markdown(md_text: str) -> tuple[str, str]:
    md = markdown.Markdown(
        extensions=["extra", "fenced_code", "tables", "codehilite", "toc"],
        extension_configs={"toc": {"permalink": False}},
    )
    html = md.convert(md_text or "")
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
    )
    return clean_html, md.toc


def strip_markdown(md_text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", md_text or "")
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"[#>*_\-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def auto_summary(content: str, max_len: int = 180) -> str:
    plain = strip_markdown(content)
    return plain[:max_len]


def highlight_keyword(text: str, keyword: str) -> str:
    if not keyword:
        return bleach.clean(text)
    escaped = re.escape(keyword)
    safe_text = bleach.clean(text)
    pattern = re.compile(escaped, re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe_text)


def match_score(text: str, keyword: str) -> int:
    if not keyword:
        return 0
    return (text or "").lower().count(keyword.lower())
