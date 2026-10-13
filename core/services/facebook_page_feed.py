"""Read the CMS-configured Facebook Page's latest image posts, without exposing access tokens.

No scraping, client-side API calls, sample posts or untrusted image proxies. Feed is optional.
Configure FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN in server environment.
"""
import json
import logging
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
FEED_CACHE_SECONDS = 30 * 60
# Only URL hosts returned by Meta that can serve public thumbnails or post links.

def _https_url(value, suffixes):
    if not isinstance(value, str) or len(value) > 2500:
        return ''
    try:
        u = urlsplit(value)
        hostname = (u.hostname or '').lower()
        if (u.scheme != 'https' or u.username or u.password or u.port not in (None, 443)
                or not any(hostname == d or hostname.endswith('.' + d) for d in suffixes)):
            return ''
    except ValueError:
        return ''
    return value


def _post_card(item):
    """Return a safe display card only when a photo thumbnail and post URL exist."""
    if not isinstance(item, dict):
        return None
    image = _https_url(item.get('full_picture'), ('fbcdn.net', 'facebook.com'))
    permalink = _https_url(item.get('permalink_url'), ('facebook.com', 'fb.watch'))
    if not image or not permalink:
        return None
    try:
        created = datetime.fromisoformat(str(item.get('created_time', '')).replace('Z', '+00:00'))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        created = None
    text = item.get('message', '')
    if not isinstance(text, str):
        text = ''
    return {'image': image, 'permalink': permalink, 'text': text[:420], 'created': created}


def get_latest_facebook_image_posts():
    """Fetch up to five newest posts with images; return [] on missing access or API failure."""
    page_id = str(getattr(settings, 'FACEBOOK_PAGE_ID', '') or '').strip()
    token = str(getattr(settings, 'FACEBOOK_PAGE_ACCESS_TOKEN', '') or '').strip()
    if not (page_id.isdigit() and token):
        return []
    key = 'public_facebook_image_posts_v1_' + page_id
    cached = cache.get(key)
    if cached is not None:
        return cached
    # Keep credentials out of URL/query strings and exception logs.
    query = urlencode({'fields': 'id,message,created_time,permalink_url,full_picture', 'limit': 15})
    url = f'https://graph.facebook.com/v26.0/{page_id}/posts?{query}'
    req = Request(url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=4) as response:
            payload = json.load(response)
        cards = []
        for item in payload.get('data', []) if isinstance(payload, dict) else []:
            card = _post_card(item)
            if card:
                cards.append(card)
            if len(cards) == 5:
                break
        cache.set(key, cards, FEED_CACHE_SECONDS)
        return cards
    except (HTTPError, URLError, OSError, ValueError, TypeError) as error:
        # Some exceptions/response objects contain URLs. Do not log their text.
        logger.warning('Facebook feed unavailable (%s)', type(error).__name__)
        cache.set(key, [], 5 * 60)
        return []
