from django.utils.html import strip_tags


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Strip HTML tags and limit length for XSS protection."""
    if not text:
        return ""
    clean = strip_tags(text).strip()
    return clean[:max_length]
