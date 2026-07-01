"""Internationalization (i18n) module for Colony AI (智衍).

Provides lightweight locale loading and translation for backend prompts and system messages.
"""

import json
import os
from typing import Any

_LOCALE_CACHE: dict[str, dict[str, Any]] = {}
_DEFAULT_LANG = "zh"

_LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")


def load_locale(lang: str) -> dict[str, Any]:
    """Load a locale JSON file and cache it.

    Args:
        lang: Language code (e.g. 'zh', 'en').

    Returns:
        The locale dictionary, or {} if not found.
    """
    if lang in _LOCALE_CACHE:
        return _LOCALE_CACHE[lang]

    path = os.path.join(_LOCALES_DIR, f"{lang}.json")
    if not os.path.isfile(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _LOCALE_CACHE[lang] = data
    return data


def set_default_lang(lang: str) -> None:
    """Set the default language globally."""
    global _DEFAULT_LANG
    _DEFAULT_LANG = lang


def _resolve_key(data: dict[str, Any], key: str) -> str | None:
    """Resolve a dotted key like 'prompts.coordinator.system' in a nested dict."""
    parts = key.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current if isinstance(current, str) else None


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Translate a key into the given language.

    Args:
        key: Dotted key path in the locale file (e.g. 'prompts.coordinator.system').
        lang: Language code. Falls back to _DEFAULT_LANG, then 'en', then the key itself.
        **kwargs: Format arguments for string interpolation.

    Returns:
        The translated string, or the key itself if not found.
    """
    lang = lang or _DEFAULT_LANG

    data = load_locale(lang)
    template = _resolve_key(data, key)

    if template is None and lang != "en":
        data = load_locale("en")
        template = _resolve_key(data, key)

    if template is None:
        # Key not found in any locale
        return key

    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template

    return template
