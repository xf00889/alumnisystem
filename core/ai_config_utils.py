"""
AI Configuration Utility Functions
Loads AI API config from the database (with caching) instead of .env.
"""
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

CACHE_KEY = 'ai_active_config'
CACHE_TTL = 300  # 5 minutes


def get_ai_config():
    """
    Get the active AI configuration from the database.
    Uses a 5-minute cache to avoid repeated DB queries.
    Returns None if no active configuration exists.
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached if cached != '__none__' else None

    try:
        from core.models.ai_config import AIConfig
        config = AIConfig.get_active_config()
        cache.set(CACHE_KEY, config if config else '__none__', CACHE_TTL)
        return config
    except Exception as e:
        logger.error(f"Error loading AI config from database: {e}")
        return None


def clear_ai_config_cache():
    """Clear the cached AI configuration. Call after saving/updating config."""
    cache.delete(CACHE_KEY)


def is_ai_enabled():
    """Return True if an active, enabled AI configuration exists."""
    config = get_ai_config()
    return bool(config and config.enabled and config.api_key)


def get_gemini_client():
    """
    Return an initialized Gemini Client using the DB config (new google-genai SDK).
    Returns (client, model_name) tuple, or (None, None) if unavailable.
    """
    config = get_ai_config()
    if not config or config.provider != 'gemini':
        return None, None
    try:
        from google import genai
        client = genai.Client(api_key=config.api_key)
        return client, config.model_name or 'gemini-2.0-flash-lite'
    except ImportError:
        logger.error("google-genai package is not installed. Run: pip install google-genai")
        return None, None
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None, None


def get_gemini_model():
    """Legacy alias — returns (client, model_name) via get_gemini_client()."""
    return get_gemini_client()
