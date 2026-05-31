"""Small in-memory cache for the active user's session data."""
from copy import deepcopy


_SESSION_CACHE = {}


def _normalize_email(email):
    return (email or "").strip().lower()


def prime_user_session(email, user=None, profile=None, settings=None):
    """Store the latest user payloads for fast access within the current app session."""
    key = _normalize_email(email)
    if not key:
        return

    entry = _SESSION_CACHE.setdefault(key, {})

    if user is not None:
        entry["user"] = deepcopy(user)
    if profile is not None:
        entry["profile"] = deepcopy(profile)
    if settings is not None:
        entry["settings"] = deepcopy(settings)


def get_cached_profile(email):
    key = _normalize_email(email)
    entry = _SESSION_CACHE.get(key, {})
    profile = entry.get("profile")
    return deepcopy(profile) if profile is not None else None


def get_cached_settings(email):
    key = _normalize_email(email)
    entry = _SESSION_CACHE.get(key, {})
    settings = entry.get("settings")
    return deepcopy(settings) if settings is not None else None


def clear_user_session(email):
    key = _normalize_email(email)
    if key:
        _SESSION_CACHE.pop(key, None)