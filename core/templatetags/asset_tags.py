"""Template helpers for cache-safe static asset URLs."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static


register = template.Library()


@lru_cache(maxsize=256)
def _content_version(file_path: str, modified_ns: int, file_size: int) -> str:
    """Return a short digest, invalidated whenever the source file changes."""
    del modified_ns, file_size
    digest = sha256()
    with Path(file_path).open("rb") as asset_file:
        for chunk in iter(lambda: asset_file.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


@register.simple_tag
def versioned_static(asset_path: str) -> str:
    """Resolve a static URL and append a source-content cache key."""
    asset_url = static(asset_path)
    source_path = finders.find(asset_path)
    if isinstance(source_path, (list, tuple)):
        source_path = source_path[0] if source_path else None
    if not source_path:
        return asset_url

    source = Path(source_path)
    try:
        stat = source.stat()
        version = _content_version(str(source), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError):
        return asset_url

    separator = "&" if "?" in asset_url else "?"
    return f"{asset_url}{separator}v={version}"
