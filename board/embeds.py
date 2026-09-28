"""Turn direct links to images / GIFs / video / audio in a post into inline media.

The forum is hosted on a phone, so people share media by pasting a link to
where it already lives (imgur, a CDN, another .onion...) instead of uploading
a copy here. The link stays in the text as-is; the media it points to is
shown under the message, loaded by the reader's browser straight from the
original host — nothing is downloaded or stored on the forum's side.
"""
import os
import re
from urllib.parse import urlsplit, urlunsplit

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.avif'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.gifv'}
AUDIO_EXTENSIONS = {'.mp3', '.ogg', '.oga', '.opus', '.wav', '.m4a', '.flac'}

MAX_EMBEDS_PER_MESSAGE = 8

# Stops at whitespace, quotes and angle brackets, so a match can never break
# out of the HTML attribute it's rendered into.
URL_RE = re.compile(r'https?://[^\s<>"\'`]+', re.IGNORECASE)
TRAILING_PUNCTUATION = '.,;:!?)]}»…'


def _media_kind(ext):
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    if ext in AUDIO_EXTENSIONS:
        return 'audio'
    return None


def extract_embeds(text, limit=MAX_EMBEDS_PER_MESSAGE):
    """Return [{'kind': 'image'|'video'|'audio', 'url': ...}, ...] for media links in text."""
    embeds = []
    seen = set()
    for match in URL_RE.finditer(text or ''):
        url = match.group(0).rstrip(TRAILING_PUNCTUATION)
        parts = urlsplit(url)
        if not parts.netloc:
            continue
        ext = os.path.splitext(parts.path)[1].lower()
        kind = _media_kind(ext)
        if kind is None:
            continue
        if ext == '.gifv':
            # imgur's ".gifv" is an HTML page wrapping an .mp4 of the same name.
            url = urlunsplit(parts._replace(path=parts.path[: -len(ext)] + '.mp4'))
        if url in seen:
            continue
        seen.add(url)
        embeds.append({'kind': kind, 'url': url})
        if len(embeds) >= limit:
            break
    return embeds
