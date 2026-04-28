"""
AI Configuration Utility Functions
Loads AI API config from the database (with caching) instead of .env.
"""
from django.core.cache import cache
import logging
from types import SimpleNamespace

import requests

logger = logging.getLogger(__name__)

CACHE_KEY = 'ai_active_config'
CACHE_TTL = 300  # 5 minutes


class _GeminiRestResponse:
    """Minimal response adapter compatible with existing Gemini parsing logic."""

    def __init__(self, payload):
        self.payload = payload or {}
        self.candidates = []

        for candidate in self.payload.get("candidates", []) or []:
            parts = []
            content = (candidate or {}).get("content", {}) or {}
            for part in content.get("parts", []) or []:
                parts.append(
                    SimpleNamespace(
                        text=part.get("text"),
                        thought=bool(part.get("thought", False)),
                    )
                )
            self.candidates.append(
                SimpleNamespace(
                    content=SimpleNamespace(parts=parts),
                )
            )

    @property
    def text(self):
        texts = []
        for candidate in self.candidates:
            for part in getattr(candidate.content, "parts", []) or []:
                if getattr(part, "thought", False):
                    continue
                if getattr(part, "text", None):
                    texts.append(part.text)
        return "".join(texts)


class _GeminiRestModels:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_content(self, model, contents, config=None):
        payload = {
            "contents": [{"parts": [{"text": str(contents)}]}],
        }

        generation_config = {}
        if config:
            if isinstance(config, dict):
                generation_config.update(config)
            else:
                for key in ("temperature", "max_output_tokens", "candidate_count", "top_p", "top_k"):
                    value = getattr(config, key, None)
                    if value is not None:
                        generation_config[key] = value

        # REST API expects maxOutputTokens instead of max_output_tokens.
        if "max_output_tokens" in generation_config:
            generation_config["maxOutputTokens"] = generation_config.pop("max_output_tokens")

        generation_config.pop("thinking_config", None)
        if generation_config:
            payload["generationConfig"] = generation_config

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": self.api_key},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return _GeminiRestResponse(response.json())


class _GeminiRestClient:
    """Drop-in fallback when google-genai import is incompatible on host."""

    def __init__(self, api_key):
        self.models = _GeminiRestModels(api_key)


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


def get_gemini_client(config_override=None):
    """
    Return an initialized Gemini Client using the DB config (new google-genai SDK).
    Returns (client, model_name) tuple, or (None, None) if unavailable.
    """
    config = config_override or get_ai_config()
    if not config or config.provider != 'gemini':
        return None, None
    try:
        from google import genai
        client = genai.Client(api_key=config.api_key)
        return client, config.model_name or 'gemini-2.0-flash-lite'
    except ImportError:
        logger.warning("google-genai not available; using Gemini REST fallback client.")
        return _GeminiRestClient(config.api_key), config.model_name or 'gemini-2.0-flash-lite'
    except Exception as e:
        logger.warning(
            "Failed to initialize google-genai client (%s). Falling back to REST client.",
            e,
        )
        return _GeminiRestClient(config.api_key), config.model_name or 'gemini-2.0-flash-lite'


def get_gemini_model():
    """Legacy alias — returns (client, model_name) via get_gemini_client()."""
    return get_gemini_client()
