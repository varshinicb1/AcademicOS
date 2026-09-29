"""Read-aloud through Sarvam's text-to-speech (INT-4, SA-7 read-aloud).

POST https://api.sarvam.ai/text-to-speech with the `api-subscription-key`
header; the body is `{"text", "language_code", "speaker", "model"}` and the
answer is `{"audios": [<base64 WAV>]}` (docs.sarvam.ai, 2026-09). Some
deployments of the API still name the language `target_language_code`; a
400/422 on the first form is retried once with that name.

Only question text a person can already see is ever sent -- never a name,
an answer or anything else about a student -- so no student data reaches the
provider (INT-4). The audio for a text is cached in memory: a class of forty
hearing the same question makes one call.
"""
from __future__ import annotations

import base64
import hashlib
import re
import threading
from collections import OrderedDict
from typing import Optional

from ..config import credential_or_none

URL = "https://api.sarvam.ai/text-to-speech"
MODEL = "bulbul:v2"
SPEAKER = "anushka"
MAX_CHARS = 1500                      # bulbul:v2's limit
_CACHE_SIZE = 256

_cache: "OrderedDict[str, bytes]" = OrderedDict()
_lock = threading.Lock()


class TTSUnavailable(RuntimeError):
    """No key configured: read-aloud is off, and the app says so."""


class TTSError(RuntimeError):
    """The provider did not give audio; the message says why."""


def api_key() -> Optional[str]:
    return credential_or_none("SARVAM_API_KEY")


def language_of(text: str) -> str:
    """hi-IN when the text is mostly Devanagari, else en-IN."""
    deva = len(re.findall(r"[ऀ-ॿ]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return "hi-IN" if deva > latin else "en-IN"


def _post(body: dict, key: str) -> "object":
    import requests
    return requests.post(URL, json=body, headers={"api-subscription-key": key}, timeout=20)


def speak(text: str, language: Optional[str] = None) -> bytes:
    """WAV audio of `text` (trimmed to MAX_CHARS at a word)."""
    key = api_key()
    if key is None:
        raise TTSUnavailable("read-aloud is not set up for this school")
    text = " ".join(text.split())
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(" ", 1)[0]
    if not text:
        raise TTSError("there is nothing to read")
    language = language or language_of(text)
    cache_key = hashlib.sha256(f"{language}|{text}".encode()).hexdigest()
    with _lock:
        if cache_key in _cache:
            _cache.move_to_end(cache_key)
            return _cache[cache_key]
    body = {"text": text, "language_code": language, "speaker": SPEAKER, "model": MODEL}
    try:
        r = _post(body, key)
        if getattr(r, "status_code", 0) in (400, 422):
            body = {**{k: v for k, v in body.items() if k != "language_code"}, "target_language_code": language}
            r = _post(body, key)
    except Exception as e:  # noqa: BLE001 - a network failure is the provider's, reported as such
        raise TTSError(f"read-aloud could not reach the speech service ({type(e).__name__})") from None
    if r.status_code != 200:
        raise TTSError(f"the speech service answered {r.status_code}")
    try:
        audio = base64.b64decode(r.json()["audios"][0])
    except (KeyError, IndexError, TypeError, ValueError):
        raise TTSError("the speech service sent no audio") from None
    with _lock:
        _cache[cache_key] = audio
        while len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return audio
