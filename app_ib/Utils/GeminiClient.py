"""
GeminiClient — thin, resilient wrapper over the Gemini REST API.

Per ALGORITHMS_FINAL: Gemini is NEVER on a read path. It only runs in background
jobs, and every call has a deterministic fallback. This client therefore never
raises to the caller — on any error (missing key, 429 quota, network, bad JSON)
it returns None and the caller uses its template fallback.
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def is_configured():
    return bool(getattr(settings, "GEMINI_API_KEY", ""))


def generate_text(prompt, temperature=0.7, max_output_tokens=512, timeout=30):
    """Return generated text, or None on any failure (caller must fall back)."""
    key = getattr(settings, "GEMINI_API_KEY", "")
    if not key:
        return None
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite")
    url = _ENDPOINT.format(model=model)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
    }
    try:
        r = requests.post(url, params={"key": key}, json=body, timeout=timeout)
        if r.status_code != 200:
            logger.warning("Gemini non-200 (%s): %s", r.status_code, r.text[:200])
            return None
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:  # noqa: BLE001 — fallback is the whole point
        logger.warning("Gemini call failed: %s", e)
        return None


def generate_json(prompt, temperature=0.7, max_output_tokens=512, timeout=30):
    """Generate text expected to be JSON; parse and return the object, else None."""
    text = generate_text(prompt, temperature, max_output_tokens, timeout)
    if not text:
        return None
    # strip ```json ... ``` fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned[cleaned.find("\n") + 1:] if "\n" in cleaned else cleaned
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except Exception:
        # last-ditch: find the first {...} or [...] block
        for op, cl in (("[", "]"), ("{", "}")):
            i, j = cleaned.find(op), cleaned.rfind(cl)
            if i != -1 and j != -1 and j > i:
                try:
                    return json.loads(cleaned[i:j + 1])
                except Exception:
                    pass
        return None
