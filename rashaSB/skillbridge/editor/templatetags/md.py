import bleach
import markdown as md_lib
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ALLOWED_TAGS = [
    "p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "strong", "em", "code", "pre", "a", "hr", "br", "blockquote",
]
_ALLOWED_ATTRS = {"a": ["href", "title"]}


@register.filter(name="markdownify")
def markdownify(value):
    """Convert markdown text to safe HTML. Empty input returns empty string."""
    if not value:
        return ""
    html = md_lib.markdown(
        str(value),
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )
    # Sanitize: strip any raw HTML (e.g. <script>) that markdown passed through.
    # ai_summary is AI-generated but we still sanitize; user notes are not passed here.
    cleaned = bleach.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
    return mark_safe(cleaned)
