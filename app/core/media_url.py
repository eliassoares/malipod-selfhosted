from __future__ import annotations

import re

_TRACKING_PREFIX_RE = re.compile(
    r"^https?://(?:"
    r"pscrb\.fm/rss/p/"
    r"|dts\.podtrac\.com/redirect\.\w+/"
    r"|www\.podtrac\.com/pts/redirect\.\w+/"
    r"|op3\.dev/e/"
    r"|pdst\.fm/e/"
    r"|chtbl\.com/track/[^/]+/"
    r")",
    re.IGNORECASE,
)


def normalize_media_url(url: str) -> str:
    """Strip known podcast tracking URL prefixes, returning the underlying media URL."""
    m = _TRACKING_PREFIX_RE.match(url)
    if m:
        return "https://" + url[m.end() :]
    return url
